from django.conf import settings
from django.forms import FileInput
from django.template.loader import render_to_string

from awesome_avatar.settings import config
from django.utils.encoding import force_str


class AvatarWidget(FileInput):

    def value_from_datadict(self, data, files, name):
        avatar_file = super(AvatarWidget, self).value_from_datadict(data, files, name)
        if not avatar_file:
            return None
            
        value = {}
        value['file'] = avatar_file
        
        x1 = data.get(name + '-x1', 0)
        y1 = data.get(name + '-y1', 0)
        x2 = data.get(name + '-x2', x1)
        y2 = data.get(name + '-y2', y1)
        
        # check for non-dimensional box, making no changes then
        if x1 == x2 or y1 == y2:
            return None
        
        ratio = data.get(name + '-ratio', 1)
        ratio = float(1 if not ratio else ratio)

        box_raw = [x1, y1, x2, y2]
        box = []

        for coord in box_raw:
            try:
                coord = int(coord)
            except ValueError:
                coord = 0

            if ratio > 1:
                coord = int(coord * ratio)
            box.append(coord)

        value['box'] = box
        return value

    def render(self, name, value, attrs=None, renderer=None):

        config.height = self.attrs['height']
        config.width = self.attrs['width']

        context = {}
        context['name'] = name
        context['config'] = config
        context['avatar_url'] = value.url if value and hasattr(value, 'url') else '/static/awesome_avatar/default.png'
        context['id'] = attrs.get('id', 'id_' + name)
        # todo fix HACK
        context['STATIC_URL'] = settings.STATIC_URL
        context['disable_preview'] = self.attrs['disable_preview']
        context['required'] = attrs.get('required', False)
        context['initial'] = value
        return render_to_string('awesome_avatar/widget.html', context)
