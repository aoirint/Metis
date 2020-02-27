from django.shortcuts import render
from django.http import HttpResponse

import os
import random
import json
import tempfile
import zipfile

from wui.models import *
# Create your views here.

# http://localhost:8000/yolo?name=mydataset&tag=タグ名&tree&onelabel
def yolo(request):
    dataset_name = os.path.basename( request.GET['name'] )
    tag_str = request.GET['tag']
    tagnames = tag_str.split(',')

    tree = request.GET.get('tree') is not None
    onelabel = request.GET.get('onelabel') is not None
    test_rate = float(request.GET.get('testrate', '0.1'))

    tags = []
    for tagname in tagnames:
        tag = MetisObjectTag.objects.get(name=tagname)
        if tag not in tags:
            tags.append(tag)

        if tree:
            for child in MetisObjectTag.objects.filter(name__startswith='%s/' % tagname):
                if child not in tags:
                    tags.append(child)

    label = -1
    categories = []
    image2objs = {}
    for tag in tags:
        if label == -1 or not onelabel:
            categories.append(tag.name)
            label += 1

        for bbox in MetisImageAnnotationBoundingBox.objects.filter(tags__in=[ tag, ]):
            image = bbox.image

            pil_image = Image.open(image.image_file.path)
            imwidth = pil_image.width
            imheight = pil_image.height

            left = bbox.left
            top = bbox.top
            width = bbox.width
            height = bbox.height

            right = left + width
            bottom = top + height

            left = max(0, left)
            top = max(0, top)
            right = min(right, imwidth-1)
            bottom = min(bottom, imheight-1)

            center_x = (left + right) / 2
            center_y = (top + bottom) / 2

            center_x = center_x / imwidth
            center_y = center_y / imheight
            width = width / imwidth
            height = height / imheight

            line = '%d %f %f %f %f' % (label, center_x, center_y, width, height)
            if image not in image2objs:
                image2objs[image] = []
            image2objs[image].append(line)

    base_dir = 'dataset/%s' % ( dataset_name, )
    train_dir = os.path.join(base_dir, 'train')
    test_dir = os.path.join(base_dir, 'test')

    train_file = os.path.join(base_dir, 'train.txt')
    test_file = os.path.join(base_dir, 'test.txt')
    data_file = os.path.join(base_dir, 'dataset.data')
    names_file = os.path.join(base_dir, 'dataset.names')
    backup_dir = 'backup/%s' % dataset_name

    train_fp = tempfile.SpooledTemporaryFile(mode='w')
    test_fp = tempfile.SpooledTemporaryFile(mode='w')
    data_fp = tempfile.SpooledTemporaryFile(mode='w')
    names_fp = tempfile.SpooledTemporaryFile(mode='w')

    outzip_fp = tempfile.SpooledTemporaryFile()
    outzip = zipfile.ZipFile(outzip_fp, 'w', zipfile.ZIP_DEFLATED)

    for category in categories:
        names_fp.write('%s\n' % category)
    names_fp.flush()
    names_fp.seek(0)
    outzip.writestr(names_file, names_fp.read())

    data_fp.write('classes = %d\n' % len(categories))
    data_fp.write('train = %s\n' % train_file)
    data_fp.write('test = %s\n' % test_file)
    data_fp.write('names = %s\n' % names_file)
    data_fp.write('backup = %s\n' % backup_dir)
    data_fp.flush()
    data_fp.seek(0)
    outzip.writestr(data_file, data_fp.read().replace('\\', '/'))


    images = list(image2objs.keys())
    n_image = len(images)
    indices = list(range(n_image))
    random.shuffle(indices)

    n_test = max(1, int(n_image * test_rate))

    info_fp_list = []
    for idx, image_idx in enumerate(indices):
        is_train = n_test < idx

        image = images[image_idx]
        objs = image2objs[image]

        in_image_path = image.image_file.path

        outdir = train_dir if is_train else test_dir
        list_fp = train_fp if is_train else test_fp

        basename = os.path.basename(image.image_file.name)
        txt_basename = os.path.splitext(basename)[0] + '.txt'

        out_image_path = os.path.join(outdir, basename)
        out_info_path = os.path.join(outdir, txt_basename)
        out_info_fp = tempfile.SpooledTemporaryFile(mode='w')
        info_fp_list.append(out_info_fp)

        outzip.write(in_image_path, arcname=out_image_path)
        list_fp.write('%s\n' % (out_image_path, ))

        for obj_line in objs:
            out_info_fp.write('%s\n' % obj_line)
        out_info_fp.flush()
        out_info_fp.seek(0)
        outzip.writestr(out_info_path, out_info_fp.read())

    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % dataset_name

    train_fp.flush()
    train_fp.seek(0)
    test_fp.flush()
    test_fp.seek(0)
    outzip.writestr(train_file, train_fp.read().replace('\\', '/'))
    outzip.writestr(test_file, test_fp.read().replace('\\', '/'))

    outzip.close()

    outzip_fp.flush()
    outzip_fp.seek(0)

    response.write(outzip_fp.read())

    return response
