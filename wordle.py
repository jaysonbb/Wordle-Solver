from nltk.corpus import words as dictionary
import re
import string
import pandas as pd
import seaborn as sns
import os
import time

LETTERS = string.ascii_lowercase

word_freq = pd.read_csv('unigram_freq.csv')

word_freq.columns = ['word','freq']

nltk_dictionary = [word.lower() for word in dictionary.words() if len(word) == 5]

wordle_words = set(nltk_dictionary + list(word_freq['word'].str.lower()))

class WordleSolver():
    def __init__(self, greens='.....', yellows=[], blacks=''):
        self.greens = greens
        self.yellow_sequence = yellows[:]
        self.blacks = blacks
        self.search_space_hist = []
        self.solve()
        
    @property
    def greens(self):
        return self._greens
    
    @greens.setter
    def greens(self, val):
        assert len(val) == 5 and isinstance(val, str)
        for char in val:
            assert char in LETTERS or char == '.'
        self._greens = val
        
    @property
    def yellow_sequence(self):
        return self._yellow_sequence
    
    @yellow_sequence.setter
    def yellow_sequence(self, val):
        assert isinstance(val, list)
        assert len(val) <= 5
        self._yellow_sequence = val
            
    @property
    def blacks(self):
        return self._blacks
    
    @blacks.setter
    def blacks(self, val):
        assert isinstance(val, str)
        assert len(val) <= 25
        for char in val:
            assert char in LETTERS
            assert val not in self.greens
            for seq in self.yellow_sequence:
                assert char not in seq
                
        dedup = set(val)
        letters = ''
        for char in dedup:
            letters += char
            
        self._blacks = letters
        
    def add_yellow(self, seq):
        assert isinstance(seq, str)
        assert len(seq) == 5
        assert len(self.yellow_sequence) + 1 <= 5
        for char in seq:
            assert char in LETTERS or char == '.'
            
        yellows = self.yellow_sequence[:]
        yellows.append(seq)
        self.yellow_sequence = yellows[:]
        
    def reset_yellows(self):
        self.yellow_sequence = []
        
    def add_blacks(self, val):
        assert isinstance(val, str)
        assert len(val) + len(self.blacks) <= 25
            
        dedup = sorted(set(self.blacks + val))
        self.blacks = ''
        for char in dedup:
            assert char in LETTERS
            if char not in self.greens:
                if len(self.yellow_sequence) == 0:
                    self.blacks += char
                else:
                    for seq in self.yellow_sequence:
                        if char not in seq:
                            self.blacks += char
                        
    def reset_blacks(self):
        self.blacks = ''
            
        
    def _possible_words(self):
        knowns = ['\w' if char == '.' else char for char in self.greens]
        pattern = f'^[{knowns[0]}][{knowns[1]}][{knowns[2]}][{knowns[3]}][{knowns[4]}]$'
        yellows = set([char for pos in self.yellow_positions for char in pos if char != '.'])
        self.possibles = []
        for word in wordle_words:
            if all([True if l in word else False for l in yellows]) and all([True if b not in word else False for b in self.blacks]):
                if re.match(pattern, word):
                    self.posibles.append(word)
                    
    def _yellow_filter(self):
        patterns = []
        for pos in self.yellow_positions:
            pattern = ''
            for char in pos:
                if char == '.':
                    pattern += f'[a-z]'
                else:
                    pattern += f'[^{char}]'
            patterns.append(pattern)
        
        self.filtered_possibles = []
        for possible in self.possibles:
            if all([True if re.match(pattern,possible) else False for pattern in patterns]):
                self.filtered_possibles.append(possible)
  
    def print_yellows(self):
        pretty_print = ''
        for seq in self.yellow_sequence:
            pretty_print += seq + ' '
            
        return pretty_print
    
    def solve(self):
        possible_words = []
        suggestions = []
        
        knowns = ['\w' if char == '.' else char for char in self.greens]
        green_pattern = f'^[{knowns[0]}][{knowns[1]}][{knowns[2]}][{knowns[3]}][{knowns[4]}]$'
        yellows = set([char for pos in self.yellow_sequence for char in pos if char != '.'])
        
        for word in wordle_words:
            if all([True if l in word else False for l in yellows]) and all([True if b not in word else False for b in self.blacks]):
                if re.match(green_pattern, word):
                    possible_words.append(word)
                    
        yellow_patterns = []
        for seq in self.yellow_sequence:
            pattern = ''
            for char in seq:
                if char == '.':
                    pattern += f'[a-z]'
                else:
                    pattern += f'[^{char}]'
            yellow_patterns.append(pattern)
        
        filtered_possibles = []
        for word in possible_words:
            if all([True if re.match(pattern, word) else False for pattern in yellow_patterns]):
                filtered_possibles.append(word)
        
        self.word_suggestions = pd.DataFrame(pd.Series(filtered_possibles), columns=['possible_word'])
        self.word_suggestions = (self.word_suggestions.merge(word_freq, left_on='possible_word', right_on='word', how='left')
                                     .drop('word',axis='columns')
                                     .drop_duplicates()
                                     .sort_values(by='freq',ascending=False)
                                     .reset_index(drop=True))
        
        self.search_space = len(self.word_suggestions)
        self.search_space_hist.append(self.search_space)
        
        return self.word_suggestions
    
    
solver = WordleSolver()

def table_gui():
    for i in range(10):
        if i >= len(solver.word_suggestions):
            print('|                         |           |              |                                 |')
        else:
            list_num = f'{i+1}.'
            word_print = '|' + list_num + ' '*(4-len(list_num)) + solver.word_suggestions['possible_word'][i] + '  |'
            try:
                freq = str(int(solver.word_suggestions['freq'][i]))
            except:
                freq = str(solver.word_suggestions['freq'][i])
            freq_print = '  '+ freq + ' '*(12-len(freq)) + '|'
            tr_for_gui = word_print + freq_print
            print(f'|                         {tr_for_gui}                                 |')


def main_gui(error):
    msg = ''
    if error:
        msg = 'ERROR: Enter a viable command.'
    yellows_for_gui = solver.print_yellows() + ' '*(32-len(solver.print_yellows()))
    blacks_for_gui = solver.blacks + ' '*(32-len(solver.blacks)-len(str(len(solver.blacks)))+1)
    greens = len(list(filter(lambda x: x != '.', solver.greens)))
    search_space_for_gui = str(solver.search_space) + ' '*(46-len(str(solver.search_space)))
    
    print('+----------------------------------- Wordle Solver  -----------------------------------+')
    print('|                                                                                      |')
    print('|            [-r] Run solver                                                           |')
    print('|                                                                                      |')
    print(f'|            [1] Change green letters      Current [{greens}] {solver.greens}                           |')
    print(f'|            [2] Add yellow sequence       Current [{len(solver.yellow_sequence)}] {yellows_for_gui}|')
    print(f'|            [3] Add black letters         Current [{len(solver.blacks)}] {blacks_for_gui}|')
    print('|                                                                                      |')
    print('|            [4] Reset yellow positions                                                |')
    print('|            [5] Reset black letters                                                   |')
    print('|                                                                                      |')
    print('|            [-n] New solver                                                           |')
    print('|            [-x] Quit                                                                 |')
    print('|                                                                                      |')
    print('|                                                                                      |')
    print(f'|                          Search Space: {search_space_for_gui}|')
    print('|                         +--------------------------+                                 |')
    print('|                         | Current word suggestions |                                 |')
    print('|                         +-----------+--------------+                                 |')
    print('|                         |    word   |  frequency   |                                 |')
    print('|                         +-----------+--------------+                                 |')
    table_gui()
    print('|                         +-----------+--------------+                                 |')
    print('|                                                                                      |')
    print('+--------------------------------------------------------------------------------------+')
    print('Navigate [ -r, 1, 2, 3, 4, 5, -n, -h, -x ]\n')
    print(msg)
    

def green_gui(error):
    msg = ''
    if error:
        msg = 'ERROR: Must enter 5 characters with letters and \'.\''
        
    yellows_for_gui = solver.print_yellows() + ' '*(32-len(solver.print_yellows()))
    blacks_for_gui = solver.blacks + ' '*(32-len(solver.blacks)-len(str(len(solver.blacks)))+1)
    greens = len(list(filter(lambda x: x != '.', solver.greens)))
    search_space_for_gui = str(solver.search_space) + ' '*(46-len(str(solver.search_space)))
    print('+---------------------------------- Change greens -------------------------------------+')
    print('|                                                                                      |')
    print('|            [-r] Run solver                                                           |')
    print('|                                                                                      |')
    print('|            [-b] Back                                                                 |')
    print(f'|            [2] Add yellow sequence       Current [{len(solver.yellow_sequence)}] {yellows_for_gui}|')
    print(f'|            [3] Add black letters         Current [{len(solver.blacks)}] {blacks_for_gui}|')
    print('|                                                                                      |')
    print('|            [4] Reset yellow positions                                                |')
    print('|            [5] Reset black letters                                                   |')
    print('|                                                                                      |')
    print(f'|                          Current greens [{greens}] {solver.greens}                                    |')
    print('|                                                                                      |')
    print('|                                                                                      |')
    print(f'|                          Search Space: {search_space_for_gui}|')
    print('|                         +--------------------------+                                 |')
    print('|                         | Current word suggestions |                                 |')
    print('|                         +-----------+--------------+                                 |')
    print('|                         |    word   |  frequency   |                                 |')
    print('|                         +-----------+--------------+                                 |')
    table_gui()
    print('|                         +-----------+--------------+                                 |')
    print('|                                                                                      |')
    print('+--------------------------------------------------------------------------------------+')
    print('Enter new greens [ ex: s..r. ]')
    print('\'-b\' to go back.\n')
    print(msg)
    

def yellow_gui(error):
    if error:
        msg = 'ERROR: Must enter 5 characters with letters and \'.\' (Note: Cannot have more than 5 yellow sequences)'
    else:
        msg = ''
        
    yellows_for_gui = solver.print_yellows() + ' '*(40-len(solver.print_yellows()))
    blacks_for_gui = solver.blacks + ' '*(32-len(solver.blacks)-len(str(len(solver.blacks)))+1)
    greens = len(list(filter(lambda x: x != '.', solver.greens)))
    search_space_for_gui = str(solver.search_space) + ' '*(46-len(str(solver.search_space)))
    print('+-------------------------------- Add yellow sequence ---------------------------------+')
    print('|                                                                                      |')
    print('|            [-r] Run solver                                                           |')
    print('|                                                                                      |')
    print(f'|            [1] Change green letters      Current [{greens}] {solver.greens}                           |')
    print('|            [-b] Back                                                                 |')
    print(f'|            [3] Add black letters         Current [{len(solver.blacks)}] {blacks_for_gui}|')
    print('|                                                                                      |')
    print('|            [4] Reset yellow positions                                                |')
    print('|            [5] Reset black letters                                                   |')
    print('|                                                                                      |')
    print(f'|                          Current yellows [{len(solver.yellow_sequence)}] {yellows_for_gui}|')
    print('|                                                                                      |')
    print('|                                                                                      |')
    print(f'|                          Search Space: {search_space_for_gui}|')
    print('|                         +--------------------------+                                 |')
    print('|                         | Current word suggestions |                                 |')
    print('|                         +-----------+--------------+                                 |')
    print('|                         |    word   |  frequency   |                                 |')
    print('|                         +-----------+--------------+                                 |')
    table_gui()
    print('|                         +-----------+--------------+                                 |')
    print('|                                                                                      |')
    print('+--------------------------------------------------------------------------------------+')
    print('Add yellow sequence [ex: d..s. ]')
    print('\'-b\' to go back\n')
    print(msg)
    
def black_gui(error):
    msg = ''
    if error:
        msg = 'ERROR: Must enter letters only. (Note: Cannot have more than 25 black letters)'
    yellows_for_gui = solver.print_yellows() + ' '*(32-len(solver.print_yellows()))
    blacks_for_gui = solver.blacks + ' '*(34-len(solver.blacks)-len(str(len(solver.blacks)))+1)
    greens = len(list(filter(lambda x: x != '.', solver.greens)))
    search_space_for_gui = str(solver.search_space) + ' '*(46-len(str(solver.search_space)))
    print('+-------------------------------- Add black letters -----------------------------------+')
    print('|                                                                                      |')
    print('|            [-r] Run solver                                                           |')
    print('|                                                                                      |')
    print(f'|            [1] Change green letters      Current [{greens}] {solver.greens}                           |')
    print(f'|            [2] Add yellow sequence       Current [{len(solver.yellow_sequence)}] {yellows_for_gui}|')
    print('|            [-b] Back                                                                 |')
    print('|                                                                                      |')
    print('|            [4] Reset yellow sequences                                                |')
    print('|            [5] Reset black letters                                                   |')
    print('|                                                                                      |')
    print(f'|                          Current black letters [{len(solver.blacks)}] {blacks_for_gui}|')
    print('|                                                                                      |')
    print('|                                                                                      |')
    print(f'|                          Search Space: {search_space_for_gui}|')
    print('|                         +--------------------------+                                 |')
    print('|                         | Current word suggestions |                                 |')
    print('|                         +-----------+--------------+                                 |')
    print('|                         |    word   |  frequency   |                                 |')
    print('|                         +-----------+--------------+                                 |')
    table_gui()
    print('|                         +-----------+--------------+                                 |')
    print('|                                                                                      |')
    print('+------------------------------------------------------------------------------------- +')
    print('Add black letters [ex. \'gtu\' or \'g\' or \'gt\' ]')
    print('WARNING: letters found in green letters or a yellow sequence will not be added.')
    print('\'-b\' to go back.\n')
    print(msg)

def green_gui_action(user_input):
    try:
        solver.greens = user_input
        return True
    except:
        return False


def yellow_gui_action(user_input):
    try:
        solver.add_yellow(user_input)
        return True
    except:
        return False

def black_gui_action(user_input):
    try:
        solver.add_blacks(user_input)
        return True
    except:
        return False

navigations = {
    '-b' : main_gui,
    '1'  : green_gui,
    '2'  : yellow_gui,
    '3'  : black_gui,
    '4'  : solver.reset_yellows,
    '5'  : solver.reset_blacks,
}

gui_actions = {
    green_gui: green_gui_action,
    yellow_gui: yellow_gui_action,
    black_gui: black_gui_action,
}

gui = navigations['-b']
error = False
clear_gui = lambda: os.system('cls')


if __name__ == '__main__':
    
    while True:
        clear_gui()
        print('\n\n\n')
        gui(error)
        error = False
        user_input = input('>>> ').lower()

        if user_input == '-x':
            clear_gui()
            break

        elif user_input == '-r':
            solver.solve()
            continue

        elif user_input == '-n':
            solver = WordleSolver()
            gui = navigations['-b']
            continue

        elif user_input == '-b':
            gui = navigations['-b']
            continue

        elif user_input == '4':
            solver.reset_yellows()
            continue

        elif user_input == '5':
            solver.reset_blacks()
            continue

            
        try:
            gui = navigations[user_input]
            continue
        except:
            pass
            
        try:
            gui_action = gui_actions[gui]
            action_success = gui_action(user_input)
            if action_success:
                error = False
                continue
        except:
            error = True

        
        
        
        
        