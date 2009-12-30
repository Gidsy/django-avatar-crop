import os.path
from django.conf import settings
from PIL import Image
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile

from avatar_crop.forms import AvatarForm, AvatarCropForm
from avatar.models import Avatar
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from avatar_crop import AVATAR_CROP_MAX_SIZE

@login_required
def avatar_crop(request, id=None):
    """
    Avatar management, creates a new avatar and makes it default
    """
    if id:
        avatar = get_object_or_404(Avatar, id=id, user=request.user)
    else:
        avatar = get_object_or_404(Avatar, user=request.user, primary=True)
    if not request.method == "POST":
        form = AvatarCropForm()
    else:
        try:
            orig = avatar.avatar.storage.open(avatar.avatar_name(AVATAR_CROP_MAX_SIZE), 'rb').read()
            image = Image.open(StringIO(orig))
        except IOError:
            return
        form = AvatarCropForm(image, request.POST)
        if form.is_valid():
            top = int(form.cleaned_data.get('top'))
            left = int(form.cleaned_data.get('left'))
            right = int(form.cleaned_data.get('right'))
            bottom = int(form.cleaned_data.get('bottom'))

            box = [ left, top, right, bottom ]
            (w, h) = image.size
            image = image.crop(box)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            thumb = StringIO()
            image.save(thumb, "JPEG")
            thumb_file = ContentFile(thumb.getvalue())
            thumb = avatar.avatar.storage.save(avatar.avatar_name('_cropped_'), thumb_file)
            Avatar.objects.filter(id=avatar.id).update(primary=False)
            new_avatar = Avatar(user=request.user, primary=True, avatar=thumb)
            new_avatar.save()
            request.user.message_set.create(message="Your new avatar has been saved successfully.")
            return HttpResponseRedirect(reverse("avatar_change"))
    if (avatar.avatar.width<=avatar.avatar.height):
        result = "width"
    else:
        result = "height"
    return render_to_response("avatar_crop/crop.html", {'AVATAR_CROP_MAX_SIZE':AVATAR_CROP_MAX_SIZE, 'dim':result, 'avatar': avatar, 'form': form}, context_instance=RequestContext(request))

