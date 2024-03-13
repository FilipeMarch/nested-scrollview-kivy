from kivy.app import App
from kivy.clock import Clock
from kivy.factory import Factory as F
from kivy.lang import Builder

from effects import DampedScrollEffect, ScrollEffect


class CustomEffect(DampedScrollEffect):
    spring_constant = 0
    edge_damping = 1


class FixedEffectY(F.EventDispatcher):
    last_sy = 0

    my_name = F.StringProperty("a")

    def _update_effect_y(self, *args):
        vp = self._viewport
        if not vp or not self.effect_y:
            return
        if self.effect_y.is_manual:
            sh = vp.height - self._effect_y_start_height
        else:
            sh = vp.height - self.height

        if sh < 1 and not (self.always_overscroll and self.do_scroll_y):
            return
        if sh != 0:
            sy = self.effect_y.scroll / sh
            if sy < -1.01:
                sy = -1.01
            if sy > 0.01:
                sy = 0.01

            if sy - self.last_sy > 0.5:
                print("JUMPED")
                sy = -self.last_sy
            elif sy - self.last_sy < -0.5:
                print("JUMPED2")
                sy = -self.last_sy

            self.scroll_y = -sy
        else:
            self.scroll_y = 1 - self.effect_y.scroll

        if "sy" in locals():
            self.last_sy = sy
        self._trigger_update_from_scroll()

    def on_scroll_y(self, *args):
        if self.scroll_y > 1:
            Clock.schedule_once(lambda *args: setattr(self, "scroll_y", 1), -1)
        elif self.scroll_y < 0:
            Clock.schedule_once(lambda *args: setattr(self, "scroll_y", 0), -1)


class BaseScroll(FixedEffectY, F.ScrollView):
    my_name = F.StringProperty("a")

    def __init__(self, **kwargs):
        super(BaseScroll, self).__init__(**kwargs)
        # Dynamically set the effect class with the custom my_name
        self.effect_cls = lambda **kw: CustomEffect(my_name=self.my_name, **kw)

    def on_my_name(self, *args):
        self.effect_cls = lambda **kw: CustomEffect(my_name=self.my_name, **kw)


class BaseRecycle(FixedEffectY, F.RecycleView):
    my_name = F.StringProperty("b")

    def __init__(self, **kwargs):
        super(BaseRecycle, self).__init__(**kwargs)
        # Dynamically set the effect class with the custom my_name
        self.effect_cls = lambda **kw: CustomEffect(my_name=self.my_name, **kw)

    def on_my_name(self, *args):
        self.effect_cls = lambda **kw: CustomEffect(my_name=self.my_name, **kw)


class RootScroll(F.ScrollView):
    my_name = F.StringProperty("c")

    def __init__(self, **kwargs):
        super(RootScroll, self).__init__(**kwargs)
        # Dynamically set the effect class with the custom my_name
        self.effect_cls = lambda **kw: ScrollEffect(my_name=self.my_name, **kw)

    def on_my_name(self, *args):
        self.effect_cls = lambda **kw: ScrollEffect(my_name=self.my_name, **kw)


kv = """
<ColoredLabel@Label>:
    bg_color: .5, .5, 0, 1
    
    canvas.before:
        Color:
            rgba: self.bg_color
        Rectangle:
            size: self.size
            pos: self.pos

<MinimalLabel@ColoredLabel>:
    size_hint_y: None
    height: self.texture_size[1]

<BaseScroll>
    do_scroll_y: True
    do_scroll_x: False

<BaseRecycle>

RootScroll:
    effect_cls: 'ScrollEffect'
    my_name: 'ROOT'

    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: self.minimum_height

        MinimalLabel:
            text: 'Outer Label\\n' * 15

        Button:
            size_hint_y: None
            height: dp(200)

        BaseRecycle:
            data: [{'text': str(x)} for x in range(1)]
            viewclass: 'ColoredLabel'
            size_hint_y: None
            height: dp(100) * len(self.data)
            my_name: '2'
            RecycleBoxLayout:
                orientation: 'vertical'
                default_size: None, dp(100)
                default_size_hint: 1, None
                size_hint_y: None
                height: max(self.minimum_height, self.parent.height)

        BaseScroll:
            size_hint_y: None
            height: dp(200)
            my_name: '3'

            MinimalLabel:
                bg_color: 0, .5, 0, 1
                text: 'Inner Label\\n' * 20

        MinimalLabel:
            text: 'Outer Label\\n' * 15

        BaseScroll:
            size_hint_y: None
            height: dp(200)
            my_name: '4'

            MinimalLabel:
                bg_color: 0, .5, 0, 1
                text: 'Inner Label\\n' * 20

        MinimalLabel:
            text: 'Outer Label\\n' * 15
"""


class TestApp(App):
    def build(self):
        return Builder.load_string(kv)


TestApp().run()
