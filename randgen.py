import random

class RandGen(random.Random):
    """ This class will randomly generate words or passwords to be used in the crawler."""

    SMALLCASE = ''.join(chr(i) for i in range(ord('a'), ord('z')+1))
    UPPERCASE = SMALLCASE.upper()
    LETTERS = SMALLCASE + UPPERCASE
    NUMBERS = ''.join(chr(i) for i in range(ord('0'), ord('9')+1))
    ALPHANUMERIC = LETTERS + NUMBERS

    def __init__(self):
        random.Random.__init__(self)
        self.seed(1)

    def getWord(self, length=8):
        return ''.join(self.choice(RandGen.LETTERS) for i in range(length))

    def getWords(self, num=2, length=8):
        return ' '.join(self.getWord(length) for i in range(num))

    def getPassword(self, length=8):
        # make sure we have at least one for each category (A a 0)
        password = [self.choice(RandGen.SMALLCASE)] + \
                [self.choice(RandGen.UPPERCASE)] + \
                [self.choice(RandGen.NUMBERS)]
        password += [self.choice(RandGen.LETTERS)
                for i in range(length-len(password))]
        self.shuffle(password)
        return ''.join(password)



