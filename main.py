from tkinter import *
from turtle import color
from googletrans import Translator
import string,re
import codecs,itertools
import nltk
from nltk.corpus import indian
from nltk.tag import tnt
import string


nltk.download("indian")
nltk.download('punkt')

def offset_to_char(c):
    return chr(c+0x0900)

def is_consonant(c):
    o=ord(c)-0x900
    return (o>=0x15 and o<=0x39)

def getSize(reg,s):
    i = 0
    for m in reg.finditer(s):
        i = i+1
    return i

def POS_Hindi(text):
    train_data = indian.tagged_sents('hindi.pos')
    tnt_pos_tagger = tnt.TnT()
    tnt_pos_tagger.train(train_data)
    tagged_words = (tnt_pos_tagger.tag(nltk.word_tokenize(text)))
    return tagged_words

class NormalizerI(object):

    BYTE_ORDER_MARK='\uFEFF'
    BYTE_ORDER_MARK_2='\uFFFE'
    WORD_JOINER='\u2060'
    SOFT_HYPHEN='\u00AD'

    ZERO_WIDTH_SPACE='\u200B'
    NO_BREAK_SPACE='\u00A0'

    ZERO_WIDTH_NON_JOINER='\u200C'
    ZERO_WIDTH_JOINER='\u200D'

    def _normalize_punctuations(self, text):

        text=text.replace(NormalizerI.BYTE_ORDER_MARK,'')
        text=text.replace('„', r'"')
        text=text.replace('“', r'"')
        text=text.replace('”', r'"')
        text=text.replace('–', r'-')
        text=text.replace('—', r' - ')
        text=text.replace('´', r"'")
        text=text.replace('‘', r"'")
        text=text.replace('‚', r"'")
        text=text.replace('’', r"'")
        text=text.replace("''", r'"')
        text=text.replace('´´', r'"')
        text=text.replace('…', r'...')

        return text


    def normalize(self,text):
        pass 

class BaseNormalizer(NormalizerI):

    def __init__(self,
            remove_nuktas=False,
            nasals_mode='do_nothing',
            do_normalize_chandras=False,
            do_normalize_vowel_ending=False):

        self.remove_nuktas=remove_nuktas
        self.nasals_mode=nasals_mode
        self.do_normalize_chandras=do_normalize_chandras
        self.do_normalize_vowel_ending=do_normalize_vowel_ending

        self._init_normalize_chandras()
        self._init_normalize_nasals()
        self._init_normalize_vowel_ending()
        #self._init_visarga_correction()
        
    def _init_normalize_vowel_ending(self):
        self.fn_vowel_ending=self._normalize_word_vowel_ending_ie
    

    def _init_normalize_chandras(self):

        substitution_offsets =\
            [
                [0x0d , 0x0f],
                [0x11 , 0x13], 
                [0x45 , 0x47], 
                [0x49 , 0x4b], 
                # [0x72 , 0x0f],

                [0x00 , 0x02],
                [0x01 , 0x02], 
            ]

        self.chandra_substitutions =  [ 
                (offset_to_char(x[0],), offset_to_char(x[1],)) 
                    for x in substitution_offsets ]

    def _normalize_chandras(self,text):
        for match, repl in self.chandra_substitutions:
            text=text.replace(match,repl)
        return text

    def _init_to_anusvaara_strict(self):
    
        pat_signatures=\
            [
                 [0x19,0x15,0x18],
                 [0x1e,0x1a,0x1d],            
                 [0x23,0x1f,0x22],                        
                 [0x28,0x24,0x27],        
                 [0x29,0x24,0x27],                    
                 [0x2e,0x2a,0x2d],                    
            ]    
        
        halant_offset=0x4d
        anusvaara_offset=0x02
        
        pats=[]
        
        for pat_signature in pat_signatures:
            pat=re.compile(r'{nasal}{halant}([{start_r}-{end_r}])'.format(
                nasal=offset_to_char(pat_signature[0],),
                halant=offset_to_char(halant_offset,),
                start_r=offset_to_char(pat_signature[1],),
                end_r=offset_to_char(pat_signature[2],),
            ))
            pats.append(pat)
        
        repl_string='{anusvaara}\\1'.format(anusvaara=offset_to_char(anusvaara_offset,))

        self.pats_repls=(pats,repl_string)
    
    def _to_anusvaara_strict(self,text):
        
        pats, repl_string = self.pats_repls
        for pat in pats:
            text=pat.sub(repl_string,text)
            
        return text

    def _init_to_anusvaara_relaxed(self):
            
        nasals_list=[0x19,0x1e,0x23,0x28,0x29,0x2e]    
        nasals_list_str=','.join([offset_to_char(x,) for x in nasals_list])
        
        halant_offset=0x4d    
        anusvaara_offset=0x02    
        
        pat=re.compile(r'[{nasals_list_str}]{halant}'.format(
                nasals_list_str=nasals_list_str,
                halant=offset_to_char(halant_offset,),
            ))
        
        repl_string='{anusvaara}'.format(anusvaara=offset_to_char(anusvaara_offset,))

        self.pats_repls = (pat,repl_string)
    
    def _to_anusvaara_relaxed(self,text):
        pat, repl_string = self.pats_repls
        return pat.sub(repl_string,text)
    

    def _init_to_nasal_consonants(self):

        pat_signatures=\
            [
                 [0x19,0x15,0x18],
                 [0x1e,0x1a,0x1d],            
                 [0x23,0x1f,0x22],                        
                 [0x28,0x24,0x27],        
                 [0x29,0x24,0x27],                    
                 [0x2e,0x2a,0x2d],                    
            ]    
        
        halant_offset=0x4d
        anusvaara_offset=0x02 
        
        pats=[]
        repl_strings=[]
        
        for pat_signature in pat_signatures:
            pat=re.compile(r'{anusvaara}([{start_r}-{end_r}])'.format(
                anusvaara=offset_to_char(anusvaara_offset,),
                start_r=offset_to_char(pat_signature[1],),
                end_r=offset_to_char(pat_signature[2],),
            ))
            pats.append(pat)
            repl_string='{nasal}{halant}\\1'.format(
                nasal=offset_to_char(pat_signature[0],),
                halant=offset_to_char(halant_offset,),
                )
            repl_strings.append(repl_string)
    
        self.pats_repls=list(zip(pats,repl_strings))

    def _to_nasal_consonants(self,text):
    
        for pat, repl in self.pats_repls:
            text=pat.sub(repl,text)
            
        return text

    def _init_normalize_nasals(self):

        if self.nasals_mode == 'to_anusvaara_strict':
            self._init_to_anusvaara_strict()
        elif self.nasals_mode == 'to_anusvaara_relaxed':
            self._init_to_anusvaara_relaxed()
        elif self.nasals_mode == 'to_nasal_consonants':
            self._init_to_nasal_consonants()

    def _normalize_nasals(self,text): 
        if self.nasals_mode == 'to_anusvaara_strict':
            return self._to_anusvaara_strict(text)
        elif self.nasals_mode == 'to_anusvaara_relaxed':
            return self._to_anusvaara_relaxed(text)
        elif self.nasals_mode == 'to_nasal_consonants':
            return self._to_nasal_consonants(text)
        else:
            return text

    
    def _normalize_word_vowel_ending_dravidian(self,word):

        if len(word)>0 and is_consonant(word[-1],):
            return word+offset_to_char(0x3e,)
        else:
            return word

    def _normalize_word_vowel_ending_ie(self,word):

        if len(word)>0 and is_consonant(word[-1],):
            return word+offset_to_char(0x4d,)
        else:
            return word 

    def _normalize_vowel_ending(self,text):
        return ' '.join([ self.fn_vowel_ending(w) for w in text.split(' ') ])

    def normalize(self,text):
        text=text.replace(NormalizerI.BYTE_ORDER_MARK,'')
        text=text.replace(NormalizerI.BYTE_ORDER_MARK_2,'')
        text=text.replace(NormalizerI.WORD_JOINER,'')
        text=text.replace(NormalizerI.SOFT_HYPHEN,'')

        text=text.replace(NormalizerI.ZERO_WIDTH_SPACE,' ') 
        text=text.replace(NormalizerI.NO_BREAK_SPACE,' ')

        text=text.replace(NormalizerI.ZERO_WIDTH_NON_JOINER, '')
        text=text.replace(NormalizerI.ZERO_WIDTH_JOINER,'')
        
        text=self._normalize_punctuations(text)

        if self.do_normalize_chandras:
            text=self._normalize_chandras(text)
        text=self._normalize_nasals(text)
        if self.do_normalize_vowel_ending:
            text=self._normalize_vowel_ending(text)
        
        return text

    def get_char_stats(self,text):    
        print(len(re.findall(NormalizerI.BYTE_ORDER_MARK,text)))
        print(len(re.findall(NormalizerI.BYTE_ORDER_MARK_2,text)))
        print(len(re.findall(NormalizerI.WORD_JOINER,text)))
        print(len(re.findall(NormalizerI.SOFT_HYPHEN,text)))

        print(len(re.findall(NormalizerI.ZERO_WIDTH_SPACE,text) ))
        print(len(re.findall(NormalizerI.NO_BREAK_SPACE,text)))

        print(len(re.findall(NormalizerI.ZERO_WIDTH_NON_JOINER,text)))
        print(len(re.findall(NormalizerI.ZERO_WIDTH_JOINER,text)))

    def correct_visarga(self,text,visarga_char,char_range):
        text=re.sub(r'([\u0900-\u097f]):','\\1\u0903',text)

def wordTokenize(text):
    hindi_pat = re.compile(r'(['+string.punctuation+r'\u0964\u0965'+r'])')
    num_pat = re.compile(r'([0-9]+ [,.:/] )+[0-9]+')
    hindi_num_pat = re.compile(r'([\u0966-\u096F]+ [,.:/] )+[\u0966-\u096F]+',re.UNICODE)
    tok_str = hindi_pat.sub(r' \1',text.replace('\t',' '))
    s=re.sub(r'[ ]+',' ',tok_str).strip(' ')
    new_s=''
    prev=0
    if(getSize(num_pat,s) != 0):
        l = num_pat.finditer(s)
    else:
        l = hindi_num_pat.finditer(s) 
    for m in l:
        start=m.start()
        end=m.end()
        if start>prev:
            new_s=new_s+s[prev:start]
            new_s=new_s+s[start:end].replace(' ','')
            prev=end
    new_s=new_s+s[prev:]
    s=new_s
    s=s.split(' ')
    return s

DELIM_PAT_DANDA=re.compile(r'[\?!\u0964\u0965]')
normallizer = BaseNormalizer(nasals_mode='to_anusvaara_strict',do_normalize_chandras=True,do_normalize_vowel_ending=True)
DELIM_PAT_NO_DANDA=re.compile(r'[\.\?!\u0964\u0965]')

CONTAINS_DANDA=re.compile(r'[\u0964\u0965]')

def is_acronym_abbvr(text):
    ack_chars =  {
     ## acronym for latin characters
      'ए', 'ऎ',
      'बी', 'बि', 
      'सी', 'सि',
      'डी', 'डि',
      'ई', 'इ',
       'एफ', 'ऎफ',
      'जी', 'जि',
      'एच','ऎच',
      'आई',  'आइ','ऐ',
      'जे', 'जॆ',
      'के', 'कॆ',
      'एल', 'ऎल',
      'एम','ऎम',
      'एन','ऎन',
      'ओ', 'ऒ',
      'पी', 'पि',
      'क्यू', 'क्यु',
      'आर', 
      'एस','ऎस',
      'टी', 'टि',
      'यू', 'यु',
      'वी', 'वि', 'व्ही', 'व्हि',
      'डब्ल्यू', 'डब्ल्यु',
      'एक्स','ऎक्स',
      'वाय',
      'जेड', 'ज़ेड',
    ##  add halant to the previous English character mappings.            
     'एफ्',
     'ऎफ्',
     'एच्',
     'ऎच्',
     'एल्',
     'ऎल्',
     'एम्',
     'ऎम्',
     'एन्',
     'ऎन्',
     'आर्',
     'एस्',
     'ऎस्',
     'एक्स्',
     'ऎक्स्',
     'वाय्',
     'जेड्', 'ज़ेड्',    

    #Indic vowels
        'ऄ',
        'अ',
        'आ',
        'इ',
        'ई',
        'उ',
        'ऊ',
        'ऋ',
        'ऌ',
        'ऍ',
        'ऎ',
        'ए',
        'ऐ',
        'ऑ',
        'ऒ',
        'ओ',
        'औ',
        'ॠ',
        'ॡ',
        
    #Indic consonants
        'क',
        'ख',
        'ग',
        'घ',
        'ङ',
        'च',
        'छ',
        'ज',
        'झ',
        'ञ',
        'ट',
        'ठ',
        'ड',
        'ढ',
        'ण',
        'त',
        'थ',
        'द',
        'ध',
        'न',
        'ऩ',
        'प',
        'फ',
        'ब',
        'भ',
        'म',
        'य',
        'र',
        'ऱ',
        'ल',
        'ळ',
        'ऴ',
        'व',
        'श',
        'ष',
        'स',
        'ह',  
        
    ## abbreviation
     'श्री',
     'डॉ',
     'कु',
     'चि',
     'सौ',
    }

    return (text in ack_chars)

def sentence_split(text):
    if CONTAINS_DANDA.search(text) is None:
        delim_pat=DELIM_PAT_NO_DANDA
    else:
        delim_pat=DELIM_PAT_DANDA
    cand_sentences=[]
    begin=0
    text = text.strip()
    for mo in delim_pat.finditer(text):
        p1=mo.start()
        p2=mo.end()
        if p1>0 and text[p1-1].isnumeric():
            continue

        end=p1+1
        s= text[begin:end].strip()
        if len(s)>0:
            cand_sentences.append(s)
        begin=p1+1

    s= text[begin:].strip()
    if len(s)>0:
        cand_sentences.append(s)

    if not delim_pat.search('.'):
        return cand_sentences
    final_sentences=[]
    sen_buffer=''        
    bad_state=False

    for i, sentence in enumerate(cand_sentences): 
        words=sentence.split(' ')
        if len(words)==1 and sentence[-1]=='.':
            bad_state=True
            sen_buffer = sen_buffer + ' ' + sentence   
        elif sentence[-1]=='.' and is_acronym_abbvr(words[-1][:-1]):
            if len(sen_buffer)>0 and  not bad_state:
                final_sentences.append(sen_buffer)
            bad_state=True
            sen_buffer = sentence
        elif bad_state:
            sen_buffer = sen_buffer + ' ' + sentence
            if len(sen_buffer)>0:
                final_sentences.append(sen_buffer)
            sen_buffer=''
            bad_state=False
        else:                    
            if len(sen_buffer)>0:
                final_sentences.append(sen_buffer)
            sen_buffer=sentence
            bad_state=False

    if len(sen_buffer)>0:
        final_sentences.append(sen_buffer)
    
    return final_sentences

class MyWindow:
    def __init__(self, win):
        self.head = Label(win,text= 'NLP Project')
        self.head.config(font=("Courier", 25))
        self.lbl1=Label(win, text='Enter Text:')
        self.lbl2=Label(win, text='Enter Hindi Text:')
        self.lbl3=Label(win, text='Translation:')
        self.lbl4=Label(win, text='Word Tokenization:')
        self.lbl5=Label(win, text='Sentence Tokenization:')
        self.lbl6=Label(win, text='Normalization:')
        self.lbl7=Label(win, text='POS Tagging:')

        self.t1=Entry()
        self.t2=Entry()
        self.t3=Entry()
        self.t4=Entry()
        self.t5=Entry()
        self.t6=Entry()
        self.t7=Entry()


        self.btn1 = Button(win, text='Add')

        self.lbl1.place(x=10, y=150)
        self.head.place(x=250, y=5)
        self.t1.place(x=250, y=150)
        self.t2.place(x=250, y=250)
        self.b1=Button(win, text='Translate', command=self.add)
        self.b2=Button(win, text='Analyse', command=self.analyse)
        self.b1.place(x=600, y=150)
        self.lbl3.place(x=10, y=200)
        self.t3.place(x=250, y=200)
        self.t4.place(x=250, y=300)
        self.t5.place(x=250, y=350)
        self.t6.place(x=250, y=400)
        self.t7.place(x=250, y=450)

        self.lbl4.place(x=10, y=300)
        self.lbl5.place(x=10, y=350)
        self.lbl6.place(x=10, y=400)
        self.lbl7.place(x=10, y=450)
        self.lbl2.place(x=10, y=250)
        self.b2.place(x=600, y=250)


        
        self.t1.config(width=50)  
        self.t3.config(width=50)    
        self.t4.config(width=50)  
        self.t5.config(width=50)  
        self.t6.config(width=50)  
        self.t7.config(width=50)  
    
        self.b1.config(font=("Courier", 12))
        self.b2.config(font=("Courier", 12))
        self.lbl1.config(font=("Courier", 12))
        self.lbl2.config(font=("Courier", 12))
        self.lbl3.config(font=("Courier", 12))
        self.lbl4.config(font=("Courier", 12))
        self.lbl5.config(font=("Courier", 12))
        self.lbl6.config(font=("Courier", 12))
        self.lbl7.config(font=("Courier", 12))
        # self.t2.config(font=("Courier", 12))

    def analyse(self):
        self.t4.delete(0, 'end')
        self.t5.delete(0, 'end')
        self.t6.delete(0, 'end')
        self.t7.delete(0, 'end')
        result = str(self.t2.get())

        self.t4.insert(END, str(wordTokenize(result)))
        self.t5.insert(END, str(sentence_split(result)))
        normal = normallizer.normalize(result)
        self.t6.insert(END, str(normal))
        self.t7.insert(END, str(POS_Hindi(result)))





    def add(self):
        self.t3.delete(0, 'end')
        translator = Translator()
        result = str(self.t1.get())
        output = translator.translate(result,src='en',dest='hi')
        self.t3.insert(END, str(output.text))

window=Tk()
mywin=MyWindow(window)
window.title('NLP Project')
window.geometry("800x800")
window.mainloop()