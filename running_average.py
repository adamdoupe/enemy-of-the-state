class RunningAverage(object):
    def __init__(self, size):
        self.vec = [0] * size
        self.epoch = -1

    # at every epoch increse, the history is reset to 0
    def add(self, v, epoch=-1):
        if epoch != self.epoch:
            self.epoch = epoch
            self.reset()
        self.vec = self.vec[1:] + [v]

    def average(self):
        return sum(self.vec) / float(len(self.vec))

    def reset(self):
        self.vec = [0] * len(self.vec)
