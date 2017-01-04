# TODO:
# - UNKNOWN_CHARS_REGEX
# - remove accents
# - test on small dataset
# - use process pool to generate full dataset *
# - generate alpabetic dataset
# - make char RNN model *
#   - test alphabetic vs arpabetic loss convergence
# - make convolutional model following Zhang
# - compare with word RNN loss


import cPickle
import re
import os
import glob

import pandas as pd
import numpy as np
import h5py


ARPABET_DICT = 'arpabet_dict.pkl'
N_RESERVED_CHARS = 3


def get_chars_in_file(filename):
    return = set([list(line.decode('utf-8')) for line in open('/Users/rob/Downloads/aclImdb/all_neg_chars.txt')][0])
    for line in open(filename).read():
        chars |= {c for c in line.decode('utf-8')}
    return chars


def make_arpabet_dict():
    """
    PREP:
        printf '%s\0' aclImdb/*/pos/*.txt | xargs -0 cat > aclImdb/all_pos.txt
        printf '%s\0' aclImdb/*/neg/*.txt | xargs -0 cat > aclImdb/all_neg.txt
        perl -C -ne'print grep {!$a{$_}++} /\X/g' aclImdb/all_neg.txt > aclImdb/all_neg_chars.txt
        perl -C -ne'print grep {!$a{$_}++} /\X/g' aclImdb/all_pos.txt > aclImdb/all_pos_chars.txt
    """
    if not os.path.exists(ARPABET_DICT):
        neg_chars = get_chars_in_file('/Users/rob/Downloads/aclImdb/all_neg_chars.txt')
        pos_chars = get_chars_in_file('/Users/rob/Downloads/aclImdb/all_pos_chars.txt')
        used_chars = {c for c in neg_chars | pos_chars}
        arpabet_chars = [c.strip() for c in open('cmudict-0.7b.symbols') if c != '']
        unused_chars = []
        i = 192
        while len(unused_chars) < len(arpabet_chars) + N_RESERVED_CHARS:
            new_char = unichr(i)
            if new_char not in used_chars:
                unused_chars.append(new_char)
            i += 1

        arpabet_map = {c: unused_chars[i] for i, c in enumerate(arpabet_chars)}
        transcription = pd.read_csv('simplified_cmudict.gz', sep='\t', header=None, names=['transcription'], index_col=0)
        print "Making arpabet dictionary..."
        arpabet_dict = {str(i).lower(): "".join([arpabet_map[c] for c in row.transcription.split()]) for i, row in transcription.iterrows()}
        #  NOTE: only using first transcription where there are multiple options
        ARPABET_REGEX = re.compile("(?u)\\b(%s)\\b" % "|".join(sorted(arpabet_dict.keys(), reverse=True)))

        arpabet_inverse_dict = {v: k for k, v in arpabet_dict.iteritems()}
        ARPABET_INVERSE_REGEX = re.compile("(?u)\\b(%s)\\b" % "|".join(sorted(arpabet_inverse_dict.keys(), reverse=True)))

        cPickle.dump(
            (
                arpabet_dict,
                arpabet_map,
                ARPABET_REGEX,
                unused_chars,
                arpabet_inverse_dict,
                ARPABET_INVERSE_REGEX
            ),
            open(ARPABET_DICT, 'w')
        )
    else:
        (
            arpabet_dict,
            arpabet_map,
            ARPABET_REGEX,
            unused_chars,
            arpabet_inverse_dict,
            ARPABET_INVERSE_REGEX
        ) = cPickle.load(open(ARPABET_DICT))

    return (
        arpabet_dict,
        arpabet_map,
        ARPABET_REGEX,
        unused_chars,
        arpabet_inverse_dict,
        ARPABET_INVERSE_REGEX
    )


(
    arpabet_dict,
    arpabet_map,
    ARPABET_REGEX,
    unused_chars,
    arpabet_inverse_dict,
    ARPABET_INVERSE_REGEX
) = make_arpabet_dict()
alphabet = u'abcdefghijklmnopqrstuvwxyz0123456789-,;.!?:\'"/|_#$%^&*~+=<>()[]{}'
ALLOWABLE_CHARS = u' ' + alphabet + "".join(arpabet_map.values())
UNKNOWN_CHARS_REGEX = re.compile(u'[^{}]'.format(re.escape(ALLOWABLE_CHARS)))
coding_chars = "".join(unused_chars[:-N_RESERVED_CHARS:]) + ALLOWABLE_CHARS
all_chars_map = pd.Series(np.arange(len(coding_chars), dtype=np.uint8), index=list(coding_chars))
all_chars_inverse_map = pd.Series(list(coding_chars), index=np.arange(len(coding_chars), dtype=np.uint8))
unknown_index = all_chars_map.index.values[N_RESERVED_CHARS-1]
maxlen = 1014
WORD_CAP = re.compile('(\s\w+)$')


def read_review(filename, arpabetic=True):
    with open(filename) as f:
        for line in f.read():
            line = WORD_CAP.sub('', line[:maxlen-1])
            # line = remove_accents(line)
            yield text_to_indecies(line.lower(), arpabetic)


def text_to_indecies(line, arpabetic=True):
    if arpabetic:
        # switch words in dictionary for phonetic transcription
        line = ARPABET_REGEX.sub(lambda mo: arpabet_dict[mo.string[mo.start():mo.end()]], line)
        # TODO: handle s' and 's better

    # mark unknown characters
    line = UNKNOWN_CHARS_REGEX.sub(unknown_index, line)
    # convert the string to a list of char indecies
    char_indecies = np.zeros(maxlen, dtype=np.uint8)
    text = all_chars_map.loc[list(line)].values
    char_indecies[:text.shape[0]] = text
    char_indecies[text.shape[0]] = 1
    return char_indecies


def reviews_to_dataset(dataset_filename='/Users/rob/Downloads/aclImdb/arpabetic.hdf'):
    # TODO: use process pool, write to index in HDF5 file
    with h5py.open(dataset_filename, 'w') as dataset:
        for d in ['train', 'test']:
            filenames = glob.glob('/Users/rob/Downloads/aclImdb/{}/???/*.txt'.format(d))
            dataset.create_dataset(
                d + '_x',
                (len(filenames), maxlen),
                dtype=np.uint8,
                # chunks=True,
                compression="gzip",
                compression_opts=7
            )
            dataset.create_dataset(
                d + '_y',
                (len(filenames),),
                dtype=np.bool,
                # chunks=True,
                compression="gzip",
                compression_opts=7
            )
            np.random.shuffle(filenames)
            for i, filename in enumerate(filenames[:100]):
                char_indecies = read_review(filename)
                if i % 10 == 0:
                    print "Processed file {}/{}".format(i, len(filenames))
                dataset[d + '_x'][i] = char_indecies
                dataset[d + '_y'][i] = 'pos' in filenames[i]

reviews_to_dataset()

def sanity_check_dataset(dataset_filename, arpabetic=True):
    with h5py.open(dataset_filename, 'r') as dataset:
        sample_indecies = lambda k: np.random.choice(dataset[k].shape[0], size=10)
        indecies = sample_indecies('train_x')
        print "Checking train..."
        one_hot_to_string(dataset['train_x'][indecies], dataset['train_y'][indecies], arpabetic)
        print "Checking test..."
        one_hot_to_string(dataset['test_x'][indecies], dataset['test_y'][indecies], arpabetic)


def one_hot_to_string(x, y, arpabetic=True):
    for i in xrange(x.shape[0]):
        line = all_chars_inverse_map.loc[x[i]]
        if arpabetic:
            line = ARPABET_INVERSE_REGEX.sub(lambda mo: arpabet_inverse_dict[mo.string[mo.start():mo.end()]], line)

        print y[i], line


def train_model(dataset_filename):
    """
    Use generator over HDF5 file.
    Compare loss of alphabetic vs hybrid model
    """
    pass
