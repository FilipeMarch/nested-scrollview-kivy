from time import time

from icecream import ic
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.metrics import sp
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.widget import Widget


class KineticEffect(EventDispatcher):
    """Kinetic effect class. See module documentation for more information."""

    my_name = StringProperty()

    velocity = NumericProperty(0)
    """Velocity of the movement.

    :attr:`velocity` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    """

    friction = NumericProperty(0.05)
    """Friction to apply on the velocity

    :attr:`friction` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.05.
    """

    value = NumericProperty(0)
    """Value (during the movement and computed) of the effect.

    :attr:`value` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    """

    is_manual = BooleanProperty(False)
    """Indicate if a movement is in progress (True) or not (False).

    :attr:`is_manual` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    """

    max_history = NumericProperty(5)
    """Save up to `max_history` movement value into the history. This is used
    for correctly calculating the velocity according to the movement.

    :attr:`max_history` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 5.
    """

    min_distance = NumericProperty(0.1)
    """The minimal distance for a movement to have nonzero velocity.

    .. versionadded:: 1.8.0

    :attr:`min_distance` is :class:`~kivy.properties.NumericProperty` and
    defaults to 0.1.
    """

    min_velocity = NumericProperty(0.5)
    """Velocity below this quantity is normalized to 0. In other words,
    any motion whose velocity falls below this number is stopped.

    .. versionadded:: 1.8.0

    :attr:`min_velocity` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.5.
    """

    std_dt = NumericProperty(0.017)
    """ std_dt
        correction update_velocity if dt is not constant

    .. versionadded:: 2.0.0

    :attr:`std_dt` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.017.
    """

    def __init__(self, **kwargs):
        self.history = []
        self.trigger_velocity_update = Clock.create_trigger(self.update_velocity, 0)
        super(KineticEffect, self).__init__(**kwargs)

    def apply_distance(self, distance):
        if abs(distance) < self.min_distance:
            self.velocity = 0
        self.value += distance

    def start(self, val, t=None):
        """Start the movement.

        :Parameters:
            `val`: float or int
                Value of the movement
            `t`: float, defaults to None
                Time when the movement happen. If no time is set, it will use
                time.time()
        """
        self.is_manual = True
        t = t or time()
        self.velocity = 0
        self.history = [(t, val)]

    def update(self, val, t=None):
        """Update the movement.

        See :meth:`start` for the arguments.
        """
        t = t or time()
        distance = val - self.history[-1][1]
        self.apply_distance(distance)
        self.history.append((t, val))
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def stop(self, val, t=None):
        """Stop the movement.

        See :meth:`start` for the arguments.
        """
        self.is_manual = False
        t = t or time()
        distance = val - self.history[-1][1]
        self.apply_distance(distance)
        newest_sample = (t, val)
        old_sample = self.history[0]
        for sample in self.history:
            if (newest_sample[0] - sample[0]) < 10.0 / 60.0:
                break
            old_sample = sample
        distance = newest_sample[1] - old_sample[1]
        duration = abs(newest_sample[0] - old_sample[0])
        self.velocity = distance / max(duration, 0.0001)
        self.trigger_velocity_update()

    def cancel(self):
        """Cancel a movement. This can be used in case :meth:`stop` cannot be
        called. It will reset :attr:`is_manual` to False, and compute the
        movement if the velocity is > 0.
        """
        self.is_manual = False
        self.trigger_velocity_update()

    def update_velocity(self, dt):
        """(internal) Update the velocity according to the frametime and
        friction.
        """
        if abs(self.velocity) <= self.min_velocity:
            self.velocity = 0
            return

        self.velocity -= self.velocity * self.friction * dt / self.std_dt
        self.apply_distance(self.velocity * dt)
        self.trigger_velocity_update()


class ScrollEffect(KineticEffect):
    """ScrollEffect class. See the module documentation for more information."""

    my_name = StringProperty()

    drag_threshold = NumericProperty("20sp")
    """Minimum distance to travel before the movement is considered as a drag.

    :attr:`drag_threshold` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 20sp.
    """

    min = NumericProperty(0)
    """Minimum boundary to use for scrolling.

    :attr:`min` is a :class:`~kivy.properties.NumericProperty` and defaults to
    0.
    """

    max = NumericProperty(0)
    """Maximum boundary to use for scrolling.

    :attr:`max` is a :class:`~kivy.properties.NumericProperty` and defaults to
    0.
    """

    scroll = NumericProperty(0)
    """Computed value for scrolling. This value is different from
    :py:attr:`kivy.effects.kinetic.KineticEffect.value`
    in that it will return to one of the min/max bounds.

    :attr:`scroll` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 0.
    """

    overscroll = NumericProperty(0)
    """Computed value when the user over-scrolls i.e. goes out of the bounds.

    :attr:`overscroll` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    """

    target_widget = ObjectProperty(None, allownone=True, baseclass=Widget)
    """Widget to attach to this effect. Even if this class doesn't make changes
    to the `target_widget` by default, subclasses can use it to change the
    graphics or apply custom transformations.

    :attr:`target_widget` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    """

    displacement = NumericProperty(0)
    """Cumulative distance of the movement during the interaction. This is used
    to determine if the movement is a drag (more than :attr:`drag_threshold`)
    or not.

    :attr:`displacement` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    """

    def reset(self, pos):
        """(internal) Reset the value and the velocity to the `pos`.
        Mostly used when the bounds are checked.
        """
        self.value = pos
        self.velocity = 0
        if self.history:
            val = self.history[-1][1]
            self.history = [(time(), val)]

    def on_value(self, *args):
        scroll_min = self.min
        scroll_max = self.max

        if scroll_min > scroll_max:
            scroll_min, scroll_max = scroll_max, scroll_min
        if self.value < scroll_min:
            self.overscroll = self.value - scroll_min
            self.reset(scroll_min)
        elif self.value > scroll_max:
            self.overscroll = self.value - scroll_max
            self.reset(scroll_max)
        else:
            self.scroll = self.value

        # ic(self.my_name, self.value, self.overscroll)

    def start(self, val, t=None):
        self.is_manual = True
        self.displacement = 0
        return super(ScrollEffect, self).start(val, t)

    def update(self, val, t=None):
        self.displacement += abs(val - self.history[-1][1])
        return super(ScrollEffect, self).update(val, t)

    def stop(self, val, t=None):
        self.is_manual = False
        self.displacement += abs(val - self.history[-1][1])
        if self.displacement <= self.drag_threshold:
            self.velocity = 0
            return
        return super(ScrollEffect, self).stop(val, t)


class DampedScrollEffect(ScrollEffect):
    """DampedScrollEffect class. See the module documentation for more
    information.
    """

    my_name = StringProperty()

    edge_damping = NumericProperty(0.25)
    """Edge damping.

    :attr:`edge_damping` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.25
    """

    spring_constant = NumericProperty(2.0)
    """Spring constant.

    :attr:`spring_constant` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 2.0
    """

    min_overscroll = NumericProperty(0.5)
    """An overscroll less than this amount will be normalized to 0.

    .. versionadded:: 1.8.0

    :attr:`min_overscroll` is a :class:`~kivy.properties.NumericProperty` and
    defaults to .5.
    """

    round_value = BooleanProperty(True)
    """If True, when the motion stops, :attr:`value` is rounded to the nearest
    integer.

    .. versionadded:: 1.8.0

    :attr:`round_value` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    """

    def update_velocity(self, dt):
        if abs(self.velocity) <= self.min_velocity and self.overscroll == 0:
            self.velocity = 0
            # why does this need to be rounded? For now refactored it.
            if self.round_value:
                self.value = round(self.value)
            return

        total_force = self.velocity * self.friction * dt / self.std_dt
        if abs(self.overscroll) > self.min_overscroll:
            total_force += self.velocity * self.edge_damping
            total_force += self.overscroll * self.spring_constant
        else:
            self.overscroll = 0

        stop_overscroll = ""
        if not self.is_manual:
            if self.overscroll > 0 and self.velocity < 0:
                stop_overscroll = "max"
            elif self.overscroll < 0 and self.velocity > 0:
                stop_overscroll = "min"

        self.velocity = self.velocity - total_force
        if not self.is_manual:
            self.apply_distance(self.velocity * dt)
            if stop_overscroll == "min" and self.value > self.min:
                self.value = self.min
                self.velocity = 0
                return
            if stop_overscroll == "max" and self.value < self.max:
                self.value = self.max
                self.velocity = 0
                return
        self.trigger_velocity_update()

    def on_value(self, *args):
        scroll_min = self.min
        scroll_max = self.max

        if scroll_min > scroll_max:
            scroll_min, scroll_max = scroll_max, scroll_min
        if self.value < scroll_min:
            self.overscroll = self.value - scroll_min
        elif self.value > scroll_max:
            self.overscroll = self.value - scroll_max
        else:
            self.overscroll = 0
        self.scroll = self.value

        # ic(self.my_name, self.value, self.overscroll)

    def on_overscroll(self, *args):
        # ic()
        self.trigger_velocity_update()

    def apply_distance(self, distance):
        os = abs(self.overscroll)
        if os:
            # ic(self.my_name)
            distance /= 1.0 + os / sp(200.0)
        super(DampedScrollEffect, self).apply_distance(distance)
