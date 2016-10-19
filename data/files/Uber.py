class TrieNode(object):
    def __init__(self):
        self.is_word = False
        self.prefix_num = 0
        self.children = {}

class Trie(object):
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        current = self.root
        for letter in word:
            if letter not in current.children:
                current.children[letter] = TrieNode()
            current = current.children[letter]
            current.prefix_num += 1
        current.is_word = True

    def search(self, word):
        current = self.root
        for letter in word:
            if letter not in current.children:
                return False
            current = current.children[letter]
        return current.is_word

    def startsWith(self, prefix):
        current = self.root
        for letter in preifx:
            if letter not in current.children:
                return False
            current = current.children[letter]
        return True

    def prefix_num(self, prefix):
        current = self.root
        for letter in prefix:
            if letter not in current.children:
                return False
            current = current.children[letter]
        return current.prefix_num

class Solution:
    # @param A : list of strings
    # @return a list of strings
    def prefix(self, A):
        trie = Trie()
        result = []
        for word in A:
            trie.insert(word)
        for word in A:
            w_length = len(word)
            for i in range(1, w_length+1):
                prefix = word[:i]
                if trie.prefix_num(prefix) == 1:
                    result.append(prefix)
                    break
        return result