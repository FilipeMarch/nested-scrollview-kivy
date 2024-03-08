from kivy.app import App
from kivy.core.window import Window
from kivy.factory import Factory as F
from kivy.lang import Builder


class NestedScrollBehavior(F.EventDispatcher):
    children_scrolls = F.ListProperty()
    inner = F.BooleanProperty(True)

    def on_touch_down(self, touch):
        if self.inner:
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.inner:
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.inner:
            return True
        return super().on_touch_up(touch)

    def check_if_should_scroll_inner(self, *args):
        if self.inner:
            return True

        if not self.children_scrolls:
            return

        if not self.collide_point(*args[0].pos):
            return

        touch = args[0]

        uid = self._get_uid()
        if uid not in touch.ud:
            # check if any of the children scrolls are being touched
            for child_scroll in self.children_scrolls:
                x, y = child_scroll.to_window(*child_scroll.pos)
                if (
                    x < touch.pos[0] < x + child_scroll.width
                    and y < touch.pos[1] < y + child_scroll.height
                ):
                    self.scroll_inner(child_scroll, touch)
                    return
        else:
            print("uid exists")

    def scroll_inner(self, child, touch):
        dy = touch.dy
        scroll_percentage = dy / self.height

        # print(f"scroll_percentage: {scroll_percentage}")
        self.effect_x.velocity = 0
        self.effect_y.velocity = 0

        if scroll_percentage < 0 and child.scroll_y == 1:
            # This means we are scrolling up
            # print("scrolling up!")
            if self.scroll_y != 1:
                if self.scroll_y - scroll_percentage > 1:
                    self.scroll_y = 1
                else:
                    self.scroll_y -= scroll_percentage / len(self.children_scrolls)

        elif scroll_percentage > 0 and child.scroll_y == 0:
            # This means we are scrolling down
            # print("scrolling down!")
            if self.scroll_y != 0:
                if self.scroll_y - scroll_percentage < 0:
                    self.scroll_y = 0
                else:
                    self.scroll_y -= scroll_percentage / len(self.children_scrolls)


class BaseScroll(F.ScrollView, NestedScrollBehavior):
    pass


class BaseRecycle(F.RecycleView, NestedScrollBehavior):
    pass


kv = """
<ColoredLabel@Label>:
    bg_color: .5, .5, 0, 1
    size_hint_y: None
    height: self.texture_size[1]

    canvas.before:
        Color:
            rgba: self.bg_color
        Rectangle:
            size: self.size
            pos: self.pos

<BaseScroll>
    on_scroll_move: root.check_if_should_scroll_inner(args[1])
    do_scroll_y: True
    do_scroll_x: False
    effect_cls: 'ScrollEffect'
    always_overscroll: False

<BaseRecycle>
    on_scroll_move: root.check_if_should_scroll_inner(args[1])

BaseScroll:
    children_scrolls: [inner_scroll.__self__, inner_scroll_2.__self__, inner_scroll_3.__self__, inner_rv.__self__]
    inner: False

    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: self.minimum_height

        ColoredLabel:
            text: 'Outer Label\\n' * 15

        Button:
            size_hint_y: None
            height: dp(200)

        BaseRecycle:
            id: inner_rv
            data: [{'text': str(x)} for x in range(20)]
            viewclass: 'Label'
            size_hint_y: None
            height: dp(200)
            effect_cls: 'ScrollEffect'
            RecycleBoxLayout:
                orientation: 'vertical'
                default_size: None, dp(100)
                default_size_hint: 1, None
                padding: dp(10), 0
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height

        BaseScroll:
            id: inner_scroll
            size_hint_y: None
            height: dp(200)

            ColoredLabel:
                bg_color: 0, .5, 0, 1
                text: 'Inner Label\\n' * 20

        ColoredLabel:
            text: 'Outer Label\\n' * 15

        BaseScroll:
            id: inner_scroll_2
            size_hint_y: None
            height: dp(200)

            ColoredLabel:
                bg_color: 0, .5, 0, 1
                text: 'Inner Label\\n' * 20

        ColoredLabel:
            text: 'Outer Label\\n' * 15

        BaseScroll:
            id: inner_scroll_3
            size_hint_y: None
            height: dp(200)

            ColoredLabel:
                bg_color: 0, .5, 0, 1
                text: 'Inner Label\\n' * 20

        ColoredLabel:
            text: 'Outer Label\\n' * 15
"""


class TestApp(App):
    def build(self):
        return Builder.load_string(kv)


TestApp().run()
