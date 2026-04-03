import argparse
import json
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
from collections import Counter
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from ml import config

def parse_xbd_label(label_path: str) -> Dict:
    with open(label_path, 'r') as f:
        data = json.load(f)
    buildings = []
    features_xy = data.get('features', {}).get('xy', [])
    for feature in features_xy:
        props = feature.get('properties', {})
        damage_type = props.get('subtype', 'no-damage')
        feature_type = props.get('feature_type', '')
        if feature_type != 'building':
            continue
        if damage_type in ['minor-damage', 'major-damage']:
            damage_type = 'severe-damage'
        if damage_type not in config.CLASS_TO_IDX:
            continue
        wkt = feature.get('wkt', '')
        if not wkt or 'POLYGON' not in wkt:
            continue
        try:
            polygon = _parse_wkt_polygon(wkt)
            xs = [p[0] for p in polygon]
            ys = [p[1] for p in polygon]
            bbox = (min(xs), min(ys), max(xs), max(ys))
        except (ValueError, IndexError):
            continue
        buildings.append({'damage': damage_type, 'damage_idx': config.CLASS_TO_IDX[damage_type], 'bbox': bbox, 'polygon': polygon, 'uid': props.get('uid', '')})
    metadata = data.get('metadata', {})
    return {'buildings': buildings, 'metadata': metadata}

def _parse_wkt_polygon(wkt: str) -> List[Tuple[float, float]]:
    inner = wkt.split('((')[1].split('))')[0]
    pairs = inner.split(',')
    coords = []
    for pair in pairs:
        parts = pair.strip().split()
        if len(parts) >= 2:
            coords.append((float(parts[0]), float(parts[1])))
    return coords

def get_image_level_label(label_path: str) -> Tuple[int, Dict]:
    parsed = parse_xbd_label(label_path)
    buildings = parsed['buildings']
    if not buildings:
        return (0, {'num_buildings': 0, 'damage_counts': {}})
    damage_counts = Counter((b['damage'] for b in buildings))
    worst_idx = max((b['damage_idx'] for b in buildings))
    return (worst_idx, {'num_buildings': len(buildings), 'damage_counts': dict(damage_counts)})

def prepare_image_level(input_dir: str, output_dir: str):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    images_dir = input_path / 'images'
    labels_dir = input_path / 'labels'
    print(f'  Input: {input_path}')
    print(f'  Output: {output_path}')
    post_labels = sorted(labels_dir.glob('*_post_disaster.json'))
    print(f'  Found {len(post_labels)} post-disaster label files')
    samples = []
    skipped = 0
    for label_path in tqdm(post_labels, desc='Parsing labels'):
        stem = label_path.stem
        pre_stem = stem.replace('_post_disaster', '_pre_disaster')
        pre_img_path = images_dir / f'{pre_stem}.png'
        post_img_path = images_dir / f'{stem}.png'
        if not pre_img_path.exists() or not post_img_path.exists():
            skipped += 1
            continue
        damage_idx, stats = get_image_level_label(str(label_path))
        samples.append({'pre_path': str(pre_img_path), 'post_path': str(post_img_path), 'label_idx': damage_idx, 'label_name': config.IDX_TO_CLASS[damage_idx], 'event': stem.rsplit('_', 2)[0], 'stats': stats})
    print(f'  Valid pairs: {len(samples)}, Skipped: {skipped}')
    dist = Counter((s['label_name'] for s in samples))
    print(f'  Class distribution: {dict(dist)}')
    if len(samples) == 0:
        print('  ERROR: No valid samples found!')
        return
    labels = [s['label_idx'] for s in samples]
    train_samples, temp_samples, train_labels, temp_labels = train_test_split(samples, labels, test_size=config.VAL_RATIO + config.TEST_RATIO, stratify=labels, random_state=42)
    relative_test = config.TEST_RATIO / (config.VAL_RATIO + config.TEST_RATIO)
    val_samples, test_samples = train_test_split(temp_samples, test_size=relative_test, stratify=temp_labels, random_state=42)
    splits = {'train': train_samples, 'val': val_samples, 'test': test_samples}
    for split_name, split_samples in splits.items():
        print(f'\n  Processing {split_name} ({len(split_samples)} samples)...')
        for cls in config.DAMAGE_CLASSES:
            (output_path / split_name / cls).mkdir(parents=True, exist_ok=True)
        counters = {cls: 0 for cls in config.DAMAGE_CLASSES}
        for sample in tqdm(split_samples, desc=f'  {split_name}'):
            cls_name = sample['label_name']
            idx = counters[cls_name]
            counters[cls_name] += 1
            event = sample['event']
            pre_dst = output_path / split_name / cls_name / f'pre_{event}_{idx:04d}.png'
            post_dst = output_path / split_name / cls_name / f'post_{event}_{idx:04d}.png'
            pre_img = cv2.imread(sample['pre_path'])
            post_img = cv2.imread(sample['post_path'])
            if pre_img is not None and post_img is not None:
                pre_resized = cv2.resize(pre_img, (config.IMG_SIZE, config.IMG_SIZE))
                post_resized = cv2.resize(post_img, (config.IMG_SIZE, config.IMG_SIZE))
                cv2.imwrite(str(pre_dst), pre_resized)
                cv2.imwrite(str(post_dst), post_resized)
        split_dist = Counter((s['label_name'] for s in split_samples))
        print(f'    Distribution: {dict(split_dist)}')
    print(f'\n  ✓ Dataset preparation complete!')
    print(f'  Output: {output_path}')

def prepare_patch_level(input_dir: str, output_dir: str, patch_size: int=128, min_building_area: float=100):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    images_dir = input_path / 'images'
    labels_dir = input_path / 'labels'
    print(f'  Extracting patches (size={patch_size}) from {input_path}')
    post_labels = sorted(labels_dir.glob('*_post_disaster.json'))
    all_patches = []
    for label_path in tqdm(post_labels, desc='Extracting patches'):
        stem = label_path.stem
        pre_stem = stem.replace('_post_disaster', '_pre_disaster')
        pre_img_path = images_dir / f'{pre_stem}.png'
        post_img_path = images_dir / f'{stem}.png'
        if not pre_img_path.exists() or not post_img_path.exists():
            continue
        pre_img = cv2.imread(str(pre_img_path))
        post_img = cv2.imread(str(post_img_path))
        if pre_img is None or post_img is None:
            continue
        parsed = parse_xbd_label(str(label_path))
        for building in parsed['buildings']:
            bbox = building['bbox']
            bx1, by1, bx2, by2 = [int(c) for c in bbox]
            area = (bx2 - bx1) * (by2 - by1)
            if area < min_building_area:
                continue
            cx = (bx1 + bx2) // 2
            cy = (by1 + by2) // 2
            half = patch_size // 2
            x1 = max(0, cx - half)
            y1 = max(0, cy - half)
            x2 = min(pre_img.shape[1], x1 + patch_size)
            y2 = min(pre_img.shape[0], y1 + patch_size)
            x1 = max(0, x2 - patch_size)
            y1 = max(0, y2 - patch_size)
            pre_patch = pre_img[y1:y2, x1:x2]
            post_patch = post_img[y1:y2, x1:x2]
            if pre_patch.shape[0] < patch_size // 2 or pre_patch.shape[1] < patch_size // 2:
                continue
            all_patches.append({'pre_patch': pre_patch, 'post_patch': post_patch, 'label_name': building['damage'], 'label_idx': building['damage_idx']})
    print(f'  Extracted {len(all_patches)} building patches')
    if not all_patches:
        print('  No patches extracted!')
        return
    labels = [p['label_idx'] for p in all_patches]
    dist = Counter((p['label_name'] for p in all_patches))
    print(f'  Distribution: {dict(dist)}')
    train_patches, temp_patches, train_labels, temp_labels = train_test_split(all_patches, labels, test_size=0.3, stratify=labels, random_state=42)
    val_patches, test_patches = train_test_split(temp_patches, test_size=0.5, stratify=temp_labels, random_state=42)
    splits = {'train': train_patches, 'val': val_patches, 'test': test_patches}
    for split_name, patches in splits.items():
        counters = {cls: 0 for cls in config.DAMAGE_CLASSES}
        for cls in config.DAMAGE_CLASSES:
            (output_path / split_name / cls).mkdir(parents=True, exist_ok=True)
        for patch in tqdm(patches, desc=f'  Saving {split_name}'):
            cls_name = patch['label_name']
            idx = counters[cls_name]
            counters[cls_name] += 1
            pre_resized = cv2.resize(patch['pre_patch'], (config.IMG_SIZE, config.IMG_SIZE))
            post_resized = cv2.resize(patch['post_patch'], (config.IMG_SIZE, config.IMG_SIZE))
            cv2.imwrite(str(output_path / split_name / cls_name / f'pre_{idx:06d}.png'), pre_resized)
            cv2.imwrite(str(output_path / split_name / cls_name / f'post_{idx:06d}.png'), post_resized)
        split_dist = Counter((p['label_name'] for p in patches))
        print(f'    {split_name}: {sum(counters.values())} patches — {dict(split_dist)}')
    print(f'\n  ✓ Patch-level dataset ready at {output_path}')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prepare xBD dataset')
    parser.add_argument('--input', '-i', type=str, required=True, help='Path to raw xBD train directory')
    parser.add_argument('--output', '-o', type=str, default=str(config.DATA_DIR / 'prepared'), help='Output directory')
    parser.add_argument('--mode', choices=['image', 'patch'], default='image', help='image=full images, patch=building-level patches')
    parser.add_argument('--patch-size', type=int, default=128, help='Patch size for patch mode')
    args = parser.parse_args()
    print('=' * 60)
    print(f'  xBD Dataset Preparation ({args.mode}-level)')
    print('=' * 60)
    if args.mode == 'image':
        prepare_image_level(args.input, args.output)
    else:
        prepare_patch_level(args.input, args.output, args.patch_size)
