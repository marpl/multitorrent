# -*- coding: utf-8 -*-


class Alerts(object):
    """
    A hierarchical alert class.

    Let's create the following alert class tree:

    foo_alert
    ├─foo_bar_alert
    └─foo_baz_alert
      └─foo_baz_paf_alert

    >>> class foo_alert(str): pass
    >>> class foo_bar_alert(foo_alert): pass
    >>> class foo_baz_alert(foo_alert): pass
    >>> class foo_baz_paf_alert(foo_baz_alert): pass

    If you listen for alerts of the `foo_baz_alert` class, you will also receive
    alerts from its subclass `foo_baz_paf_alert`, but not from its parent
    `foo_alert` or its sibling `foo_bar_alert`. Demonstration:

    >>> def p(s): print(s)
    >>> a = Alerts()
    >>> a.on(foo_baz_alert, p)  # Print the alerts of the `foo_baz_alert` tree
    >>> a.emit(foo_baz_alert('received foo_baz_alert'))
    received foo_baz_alert
    >>> a.emit(foo_baz_paf_alert('received foo_baz_paf_alert'))
    received foo_baz_paf_alert
    >>> a.emit(foo_alert('received foo_alert'))  # Nothing is printed
    >>> a.emit(foo_bar_alert('received foo_bar_alert'))  # Nothing is printed
    """

    def __init__(self, *args, **kwargs):
        super(Alerts, self).__init__(*args, **kwargs)
        self.alert_callbacks = {}

    def emit(self, alert):
        for cls in alert.__class__.__mro__:
            if not cls.__name__.endswith('_alert'):
                return
            for f in self.alert_callbacks.get(cls, []):
                f(alert)

    def on(self, alert_class, callback):
        self.alert_callbacks.setdefault(alert_class, []).append(callback)
