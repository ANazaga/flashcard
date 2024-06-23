from flask import Flask
from flask import render_template,redirect,url_for,request,Response
import pickle
import json
from collections import OrderedDict
import os
import webbrowser
import pyautogui

app = Flask(__name__)

class Card:
   def __init__(self,theme,front=None,back=None,level=1):
      self.theme = theme
      self.front = front
      self.back = back
      self.card_id = (self.theme+self.front).encode().hex()
      self.level = level
      cards.add_card(self)
      cards.update_collection()

   def update_card_id(self):
      self.card_id = (self.theme+self.front).encode().hex()

class CardCollection(OrderedDict):
   def add_card(self,card):
      self[card.theme][card.card_id] = card
      self.update_collection()

   def add_theme(self,theme):
      self[theme] = OrderedDict()
      self.update_collection()

   def del_card(self,card):
      self[card.theme].pop(card.card_id)
      self.update_collection()

   def del_theme(self,theme):
      self.pop(theme)
      self.update_collection()

   def rename_theme(self,theme,new_theme):
      self[new_theme] = self.pop(theme)
      for card in list(self[new_theme].values()):
         card.theme = new_theme
         card.update_card_id()
      self.update_collection()

   def move_card(self,old_theme,card_id,new_theme):
      card = self[old_theme].pop(card_id)
      Card(new_theme, card.front, card.back, card.level)
      self.update_collection()

   def get_levels(self,theme):
      levels = {}
      for t,c in list(self.items()):
         levels[t] = OrderedDict([(0,list(self[t].values()))])
         levels[t][0] = list(self[t].values())
         for c_id,cc in list(self[t].items()):
            levels[t].setdefault(cc.level,[]).append(cc)
         levels[t] = OrderedDict(sorted(levels[t].items()))
      return levels[theme]

   def update_collection(self):
      with open('data_collection.pkl',"wb") as file:
         pickle.dump(self,file)


if os.path.exists('data_collection.pkl'):
   with open('data_collection.pkl','rb') as file:
      cards = pickle.load(file)
else:
   cards = CardCollection()
   with open('data_collection.pkl','wb') as file:
      pickle.dump(cards,file)

@app.route('/')
def home():
   return render_template('home.html',themes=list(cards.keys()))

@app.route('/new_theme',methods=['GET','POST'])
def new_theme():
   if request.method == "GET":
      return render_template('new_theme.html')
   elif request.method == 'POST':
      new_theme = request.form.get('new_theme')
      changed_theme = request.form.get('changed_theme')
      cards_list = list(cards.keys())
      if (new_theme in cards_list) and (changed_theme not in cards_list) and changed_theme:
         cards.rename_theme(new_theme,changed_theme)
      elif new_theme and new_theme not in cards_list:
         cards.add_theme(new_theme)
      return redirect('/')

@app.route('/<theme>',methods=["GET","POST"])
def theme(theme):
   if request.method == "GET":
      return render_template('theme.html',content={"theme":theme,"cards":list(cards[theme].values())})
   elif request.method == "POST":
      cards.del_theme(theme)
      return redirect('/')

@app.route('/card_view/<theme>/<card_id>',methods=["GET"])
def card_view(theme,card_id):
   if request.method == "GET":
      return render_template('card_view.html',card=cards[theme][card_id])

@app.route('/<theme>/<card_id>',methods=["POST"])
def del_card(theme,card_id):
   if request.method == "POST":
      cards.del_card(cards[theme][card_id])
      return redirect(url_for('theme',theme=theme))

@app.route('/move_card/<old_theme>/<card_id>',methods=["GET","POST"])
def move_card(old_theme,card_id):
   if request.method == "GET":
      print(cards)
      return render_template('move_card.html',
         content=dict(old_theme=old_theme,
            card_id=card_id,
            themes=list(cards.keys())
            )
         )
   elif request.method == "POST":
      to_theme = request.form.get("to_theme")
      cards.move_card(old_theme,card_id,to_theme)
      print(cards)
      return redirect('/')

@app.route('/<theme>/new_card',methods=['GET','POST'])
def new_card(theme):
   if request.method == "GET":
      return render_template('new_card.html',theme=theme)
   elif request.method == 'POST':
      new_card = request.form
      if new_card:
         Card(theme,new_card.get('front'),new_card.get('back'),int(new_card.get('level','1')))
      return redirect(url_for('theme',theme=theme))

@app.route('/edit_card/<referrer>/<theme>/<card_id>',methods=["GET","POST"])
def edit_card(referrer,theme,card_id):
   if request.method == "GET":
      return render_template('edit_card.html',
         content={'card':cards[theme][card_id],'referrer':referrer})
   elif request.method == "POST":
      card_form = request.form
      cards[theme].pop(card_id)
      Card(theme,card_form.get('front'),card_form.get('back'),int(card_form.get('level')))
      if referrer == "theme":
         return redirect(f'/{theme}')
      else:
         return redirect(f'/practice/{theme}/{referrer}')

@app.route('/practice/<theme>/<int:le>',methods=["GET","POST"])
def practice(theme,le):
   levels = cards.get_levels(theme)
   if levels:
      if levels.get(le):
         le=le
      else:
         le=0
      return render_template('practice.html',
         content={"theme":theme,
                  "level":le,
                  "card":levels[le][0],
                  "card_numbers":levels})
   else:
      return redirect('/')

@app.route('/practice/<theme>/<int:le>/next',methods=["POST"])
def practice_buttons(theme,le):
   card = cards.get_levels(theme)[le][0]
   if request.form.get('next'):
      deleted_card = card
      cards.del_card(card)
      cards.add_card(deleted_card)
   elif request.form.get('inc'):
      if card.level < 3:
         card.level += 1
         cards.update_collection()
   elif request.form.get('dec'):
      if card.level > 1:
         card.level -= 1
         cards.update_collection()
   elif request.form.get('del'):
      cards.del_card(card)
   return redirect(url_for('practice',theme=theme,le=le))

@app.route('/practice/<theme>',methods=["POST"])
def level_choser(theme):
   level = request.form.get('level')
   return redirect(url_for('practice',theme=theme,le=level))

@app.route('/shutdown',methods=['GET'])
def shutdown():
   pyautogui.hotkey('ctrl', 'w')
   process_name = 'flashcard_flask.exe'
   result = os.system(f"taskkill /f /im {process_name}")

webbrowser.open_new_tab("http://127.0.0.1:5000/")

if __name__ == '__main__':
   app.run()