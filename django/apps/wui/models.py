from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

import os
import json
import hashlib
from PIL import Image, ImageDraw, ImageFont
import io

# Create your models here.

# decorator
def upload_save(func):
    def wrapper(*args, **kwargs):
        self = args[0]

        if self.id is None:
            saved = []
            for f in self.__class__._meta.get_fields():
                if isinstance(f, models.FileField):
                    saved.append((f.name, getattr(self, f.name)))
                    setattr(self, f.name, None)

            func(*args, **kwargs)

            for name, val in saved:
                setattr(self, name, val)
        func(*args, **kwargs)

    return wrapper

# functions
METIS_IMAGE_DIR = 'images'
METIS_IMAGE_DISPLAY_DIR = 'images_display'
def getext(filename):
    _, ext = os.path.splitext(filename)
    if len(ext) == 0:
        return '.png'
    return ext

def get_metis_image_upload_path(instance, filename):
    return os.path.join(METIS_IMAGE_DIR, '%d%s' % (instance.id, getext(filename)))
def get_metis_image_display_upload_path(instance, filename):
    return os.path.join(METIS_IMAGE_DISPLAY_DIR, '%d%s' % (instance.id, getext(filename)))

# models
class MetisImage(models.Model):
    image_file = models.ImageField(upload_to=get_metis_image_upload_path)
    image_display_file = models.ImageField(upload_to=get_metis_image_display_upload_path, null=True)
    thumbnail = ImageSpecField(
        source='image_file',
        processors=[ ResizeToFill(256, 256) ],
        format='jpeg'
    )
    thumbnail_display = ImageSpecField(
        source='image_display_file',
        processors=[ ResizeToFill(256, 256) ],
        format='jpeg'
    )

    hash = models.TextField()
    tags = models.ManyToManyField('MetisObjectTag')

    source_page_url = models.URLField(default=None, null=True)
    source_raw_url = models.URLField(default=None, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def tags_update_tagify_json(self, tagify_json):
        with transaction.atomic():
            self.tags.clear()

            for tag_data in tagify_json:
                name = tag_data['value']
                tag, created = MetisObjectTag.objects.get_or_create(name=name)

                self.tags.add(tag)

    def tags_tagify_json(self):
        ret = []
        for tag in self.tags.all():
            ret.append({
                'value': tag.name,
            })
        return json.dumps(ret)

    @upload_save
    def save(self, *args, **kwargs):
        self.update_display_image()
        super(self.__class__, self).save(*args, **kwargs)

    def update_display_image(self):
        if not self.image_file:
            return
        image_path = self.image_file.path # Invalid image_file.path
        if not os.path.exists(image_path):
            return

        bboxes = MetisImageAnnotationBoundingBox.objects.filter(image=self)

        img = Image.open(image_path).convert('RGB')
        format = img.format
        if img.format is not None:
            content_type = 'image/%s' % img.format.lower()
            filename = os.path.basename(self.image_file.name)
        else:
            format = 'jpeg'
            content_type = 'image/jpeg'
            root = os.path.splitext(os.path.basename(self.image_file.name))[0]
            filename = root + '.jpg'

        max_side = max(img.width, img.height)
        line_width = max(max_side // 100, 1)
        font_size = max(max_side // 40, 1)

        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(settings.MONOSPACED_FONT, font_size)
        COLOR_WHITE = (255, 255, 255)
        COLOR_BLACK = (0, 0, 0)
        for bbox in bboxes:
            id = bbox.id
            color = tuple(hashlib.md5(str(id).encode('ascii')).digest()[:3])

            draw.rectangle((bbox.left, bbox.top, bbox.left+bbox.width, bbox.top+bbox.height), outline=color, width=line_width)

            text = bbox.tag.name
            textsize = draw.textsize(text, font=font)
            draw.rectangle((bbox.left, bbox.top, bbox.left+textsize[0], bbox.top+textsize[1]), fill=color)

            textcolor = COLOR_BLACK if max(color) > 127 else COLOR_WHITE
            draw.text((bbox.left, bbox.top), text, font=font, fill=textcolor)


        bio = io.BytesIO()
        img.save(bio, format=format)

        uploaded_file = SimpleUploadedFile(name=filename, content=bio.getvalue(), content_type=content_type)

        self.image_display_file = uploaded_file

@receiver(post_delete, sender=MetisImage)
def after_delete_metis_image(sender, instance, **kwargs):
    instance.image_file.delete(False)


class MetisImageSet(models.Model):
    name = models.TextField()
    images = models.ManyToManyField(MetisImage)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class MetisObjectTag(models.Model):
    name = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def tree(self):
        parent_basenames = self.name.split('/')[:-1]
        ret = []
        for idx, basename in enumerate(parent_basenames):
            name = '/'.join(parent_basenames[:idx+1])
            tag, created = MetisObjectTag.objects.get_or_create(name=name)
            ret.append(tag)
        ret.append(self)

        return ret


class MetisImageAnnotationBoundingBox(models.Model):
    image = models.ForeignKey(MetisImage, on_delete=models.CASCADE, related_name='bboxes')
    tags = models.ManyToManyField('MetisObjectTag')

    left = models.IntegerField()
    top = models.IntegerField()
    width = models.IntegerField()
    height = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def tag(self):
        return self.tags.first()
    @property
    def area(self):
        return self.width * self.height
    @property
    def area_rate(self):
        return self.area / (self.image.image_file.width * self.image.image_file.height)
    @property
    def area_percentage(self):
        return self.area_rate * 100

    def tags_update_tagify_json(self, tagify_json):
        with transaction.atomic():
            self.tags.clear()

            for tag_data in tagify_json:
                name = tag_data['value']
                tag, created = MetisObjectTag.objects.get_or_create(name=name)

                self.tags.add(tag)

    def tags_tagify_json(self):
        ret = []
        for tag in self.tags.all():
            ret.append({
                'value': tag.name,
            })
        return json.dumps(ret)

# TODO: MetisImageSegmentation(data as ImageField)
