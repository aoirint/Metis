from django import forms

class NewImageForm(forms.Form):
    image = forms.ImageField(
        label='Image File',
        required=True,
        widget=forms.ClearableFileInput(
            attrs={
                'id': 'new_image_input',
                'form': 'new_image_form',
                # 'style': 'opacity: 0; position: absolute; left:0; top:0; display: block; width: 100%; height: 100%;',
                'multiple': True,
            },
        ),
    )
    tags = forms.CharField(
        label='Image Tags',
        required=True,
        widget=forms.TextInput(
            attrs={
                'id': 'tags_input',
                'form': 'new_image_form',
                'placeholder': 'Tags',
            },
        ),
    )
    source_page_url = forms.URLField(
        label='Source Page URL',
        required=False,
        widget=forms.URLInput(
            attrs={
                'id': 'source_page_url_input',
                'form': 'new_image_form',
                'placeholder': 'Source Page URL',
            },
        ),
    )
    source_raw_url = forms.URLField(
        label='Source Raw URL',
        required=False,
        widget=forms.URLInput(
            attrs={
                'id': 'source_page_raw_input',
                'form': 'new_image_form',
                'placeholder': 'Source Raw URL',
            },
        ),
    )

class DeleteImageForm(forms.Form):
    post_type = forms.CharField(
        label='Post Type',
        required=True,
        widget=forms.HiddenInput(
            attrs={
                'id': 'type_input',
                'form': 'delete_image_form',
            },
        ),
        initial='delete_image',
    )

class EditImageForm(forms.Form):
    post_type = forms.CharField(
        label='Post Type',
        required=True,
        widget=forms.HiddenInput(
            attrs={
                'id': 'type_input',
                'form': 'edit_image_form',
            },
        ),
        initial='edit_image',
    )
    tags = forms.CharField(
        label='Image Tags',
        required=True,
        widget=forms.TextInput(
            attrs={
                'id': 'tags_input',
                'form': 'edit_image_form',
                'placeholder': 'Tags',
            },
        ),
    )
    source_page_url = forms.URLField(
        label='Source Page URL',
        required=False,
        widget=forms.URLInput(
            attrs={
                'id': 'source_page_url_input',
                'form': 'edit_image_form',
                'placeholder': 'Source Page URL',
            },
        ),
    )
    source_raw_url = forms.URLField(
        label='Source Raw URL',
        required=False,
        widget=forms.URLInput(
            attrs={
                'id': 'source_page_raw_input',
                'form': 'edit_image_form',
                'placeholder': 'Source Raw URL',
            },
        ),
    )

class EditBoundingBoxForm(forms.Form):
    post_type = forms.CharField(
        label='Post Type',
        required=True,
        widget=forms.HiddenInput(
            attrs={
                'id': 'type_input',
                'form': 'edit_bbox_form',
            },
        ),
        initial='edit_bbox',
    )

    tags = forms.CharField(
        label='Image Tags',
        required=True,
        widget=forms.TextInput(
            attrs={
                'id': 'tags_input',
                'form': 'edit_bbox_form',
                'placeholder': 'Tags',
            },
        ),
    )
    left = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={
                'id': 'left_input',
                'form': 'edit_bbox_form',
            },
        ),
    )
    top = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={
                'id': 'top_input',
                'form': 'edit_bbox_form',
            },
        ),
    )
    width = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={
                'id': 'width_input',
                'form': 'edit_bbox_form',
            },
        ),
    )
    height = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={
                'id': 'height_input',
                'form': 'edit_bbox_form',
            },
        ),
    )

class DeleteBoundingBoxForm(forms.Form):
    post_type = forms.CharField(
        label='Post Type',
        required=True,
        widget=forms.HiddenInput(
            attrs={
                'id': 'type_input',
                'form': 'delete_bbox_form',
            },
        ),
        initial='delete_bbox',
    )
