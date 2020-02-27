from django.shortcuts import render, redirect
from django.db import transaction
import json
import hashlib

from wui.models import *
from wui.forms import *

# Create your views here.
def index(request):
    return redirect('wui:list_image')

def list_image(request):
    images = MetisImage.objects.all().order_by('-created_at')
    # for image in images:
    #     image.save()

    return render(request, 'list_image.html', {
        'images': images,
    })

def new_image(request):
    if request.method == 'POST':
        form = NewImageForm(request.POST, request.FILES)
        if form.is_valid():
            image_files = request.FILES.getlist('image')
            tagify_json = json.loads(form.cleaned_data['tags'])
            source_page_url = form.cleaned_data['source_page_url'] or None
            source_raw_url = form.cleaned_data['source_raw_url'] or None

            with transaction.atomic():
                for image_file in image_files:
                    m = hashlib.sha256()
                    for chunk in image_file.chunks():
                        m.update(chunk)

                    hash = m.hexdigest()
                    image = MetisImage.objects.filter(hash=hash).first() # Surppres duplication
                    if image is None:
                        image = MetisImage(image_file=image_file, hash=hash)
                        image.save()

                        image.tags_update_tagify_json(tagify_json)
                        image.source_page_url = source_page_url
                        image.source_raw_url = source_raw_url

                        image.update_display_image()
                        image.save()

                if len(image_files) == 1:
                    return redirect('wui:edit_image', id=image.id)
                return redirect('wui:list_image')

    return render(request, 'new_image.html', {
        'new_image_form': NewImageForm(),
    })

def edit_image(request, id):
    image = MetisImage.objects.get(id=id)

    if request.method == 'POST':
        post_type = request.POST['post_type']

        if post_type == 'edit_image':
            form = EditImageForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    tagify_json = json.loads(form.cleaned_data['tags'])
                    image.tags_update_tagify_json(tagify_json)

                    image.source_page_url = form.cleaned_data['source_page_url'] or None
                    image.source_raw_url = form.cleaned_data['source_raw_url'] or None

                    image.update_display_image()

                    image.save()

        elif post_type == 'delete_image':
            form = DeleteImageForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    image.delete()

                    return redirect('wui:index')

    edit_image_form = EditImageForm()
    edit_image_form.fields['tags'].initial = image.tags_tagify_json()
    edit_image_form.fields['source_page_url'].initial = image.source_page_url
    edit_image_form.fields['source_raw_url'].initial = image.source_raw_url

    return render(request, 'edit_image.html', {
        'edit_image_form': edit_image_form,
        'delete_image_form': DeleteImageForm(),
        'image': image,
    })

def edit_bbox_image(request, image_id, bbox_id=None):
    image = MetisImage.objects.get(id=image_id)
    bbox = MetisImageAnnotationBoundingBox.objects.get(id=bbox_id, image__id=image_id) if bbox_id is not None else None

    if request.method == 'POST':
        post_type = request.POST['post_type']

        if post_type == 'edit_bbox':
            form = EditBoundingBoxForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    tagify_json = json.loads(form.cleaned_data['tags'])

                    left = form.cleaned_data['left']
                    top = form.cleaned_data['top']
                    width = form.cleaned_data['width']
                    height = form.cleaned_data['height']

                    if bbox is None:
                        bbox = MetisImageAnnotationBoundingBox(image=image)

                    bbox.left = left
                    bbox.top = top
                    bbox.width = width
                    bbox.height = height

                    bbox.save()

                    bbox.tags_update_tagify_json(tagify_json)

                    image.update_display_image()
                    image.save()

                    return redirect('wui:edit_image', id=image.id)

        elif post_type == 'delete_bbox':
            form = DeleteBoundingBoxForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    bbox = MetisImageAnnotationBoundingBox.objects.get(id=bbox_id, image__id=image_id)
                    bbox.delete()

                    return redirect('wui:edit_image', id=image.id)

    edit_bbox_form = EditBoundingBoxForm()
    if bbox is not None:
        initial_top = bbox.top
        initial_left = bbox.left
        initial_width = bbox.width
        initial_height = bbox.height
        initial_tags = bbox.tags_tagify_json()
    else:
        initial_top = 0
        initial_left = 0
        initial_width = image.image_file.width
        initial_height = image.image_file.height
        initial_tags = None

    edit_bbox_form.fields['tags'].initial = initial_tags
    edit_bbox_form.fields['top'].initial = initial_top
    edit_bbox_form.fields['left'].initial = initial_left
    edit_bbox_form.fields['width'].initial = initial_width
    edit_bbox_form.fields['height'].initial = initial_height

    return render(request, 'edit_bbox_image.html', {
        'edit_bbox_form': edit_bbox_form,
        'delete_bbox_form': DeleteBoundingBoxForm(),
        'image': image,
    })
