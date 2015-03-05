
class Progress(object):
    """
    Keeps track of progress by range.

    The add() method returns False if its start or length arguments are
    incorrect, or if the specified range was already completed.

    Example:
    >>> p = Progress(100)
    >>> print(p)
    0%
    >>> p.is_complete
    False
    >>> p.add(40, 20)
    True
    >>> print(p)
    20%
    >>> p.have
    [(40, 60)]
    >>> p.add(45, 10)
    False
    >>> p.add(20, 20)
    True
    >>> print(p)
    40%
    >>> p.have
    [(20, 60)]
    >>> p.add(90, 10)
    True
    >>> print(p)
    50%
    >>> p.have
    [(20, 60), (90, 100)]
    >>> p.add(60, 30)
    True
    >>> print(p)
    80%
    >>> p.have
    [(20, 100)]
    >>> p.add(0, 20)
    True
    >>> print(p)
    100%
    >>> p.have
    [(0, 100)]
    >>> p.is_complete
    True
    """

    def __init__(self, size):
        self.have = []
        self.is_complete = False
        self.size = size

    def add(self, start, length):
        # Check arguments
        end = start + length
        if start >= self.size or end > self.size:
            return False  # Invalid block start and/or length

        # Insert in order
        inserted = False
        for i, have in enumerate(self.have):
            if start >= have[0] and end <= have[1]:
                return False  # We already have that data
            elif start <= have[0]:
                self.have.insert(i, (start, end))
                inserted = True
                break
        if not inserted:
            self.have.append((start, end))

        # Fold
        prev = self.have[0]
        a = [prev]
        i = 0
        for cur in self.have[1:]:
            if cur[0] <= prev[1]:
                cur = a[i] = (min(cur[0], prev[0]), max(cur[1], prev[1]))
            else:
                a.append(cur)
                i += 1
            prev = cur
        self.have = a

        # Check if complete and return
        if self.have == [(0, self.size)]:
            self.is_complete = True
        return True

    def __str__(self):
        p = sum(a[1] - a[0] for a in self.have)/float(self.size)*100
        return '{:.3g}%'.format(p)
