from flask import Flask
from flask import render_template,redirect,url_for,request
import json
from collections import OrderedDict
import os
app = Flask(__name__)

class Card(object):
   def __init__(self,theme=None,front=None,back=None,level=1):
      if theme in themes:
         self.theme = theme
      else:
         themes.append(theme)
         self.theme = theme
      self.front = front
      self.back = back
      self.card_id = (self.theme+self.front).encode().hex()
      self.level = level
      cards.add_card(self)
      cards.update_json()


class CardCollection(OrderedDict):
   def get_values(self):
      return [[i,v.front,v.back,v.theme,v.level] for i,v in list(self.items())]
   def get(self):
      return {i[0]:{"front":i[1],
               "back":i[2],
               "theme":i[3],
               "level":i[4]} for i in self.get_values()}
   def get_by_theme(self):
      return {t:[v for i,v in list(self.items()) if v.theme==t] for t in themes}
   def get_levels(self):
      l = {}
      for i,c in list(self.get_by_theme().items()):
         l[i] = {d:[j for j in c if j.level==d] for d in range(1,4)}
         l[i][0] = c
      return l

   def remove_theme(self,theme):
      for i in [i for i,v in list(self.items()) if v.theme==theme]:
         self.pop(i)
         self.update_json()
   # def change_themes(self,old_theme,new_theme):
   #    for i,v in list(self.items()):
   #       if v.theme == old_theme:
   #          v.theme = new_theme

   def del_card(self,index):
      self.pop(index)
      self.update_json()
   def add_card(self,card):
      if card not in list(cards.values()):
         self[card.card_id] = card
      elif card in list(cards.values()):
         self[card.card_id] = card
      self.update_json()

   def update_json(self):
      with open('json_cards.json',"w") as file:
         json.dump(self.get(),file)


themes = []
cards = CardCollection()

with open('json_cards.json','r') as file:
   json_cards = json.load(file)
for i in list(json_cards.values()):
   Card(i['theme'],i['front'],i['back'],i['level'])
print(cards)


@app.route('/')
def home(l=themes):
   return render_template('home.html',l=l)

@app.route('/new_theme',methods=['GET','POST'])
def new_theme():
   if request.method == "GET":
      return render_template('new_theme.html')
   elif request.method == 'POST':
      # global themes
      new_theme = request.form.get('new_theme')
      if new_theme and new_theme not in themes:
         themes.append(new_theme)
      return redirect('/')

@app.route('/<theme>',methods=["GET","POST"])
def theme(theme):
   global cards
   if request.method == "GET":
      return render_template('theme.html',content={"theme":theme,"cards":cards.get_by_theme()[theme]})
   elif request.method == "POST":
      global themes
      themes.remove(theme)
      cards.remove_theme(theme)
      return redirect(url_for('home'))

@app.route('/<theme>/<card_id>',methods=["POST"])
def del_card(theme,card_id):
   if request.method == "POST":
      cards.del_card(card_id)
      return redirect(url_for('theme',theme=theme))

@app.route('/<theme>/new_card',methods=['GET','POST'])
def new_card(theme):
   if request.method == "GET":
      return render_template('new_card.html',theme=theme)
   elif request.method == 'POST':
      new_card = request.form
      if new_card:
         Card(theme,new_card.get('front'),new_card.get('back'),int(new_card.get('level','1')))
      return redirect(url_for('theme',theme=theme))

@app.route('/practice/<theme>/<le>',methods=["GET","POST"])
def practice(theme,le):
   if cards.get_by_theme()[theme]:
      if cards.get_levels()[theme][int(le)]:
         le=le
      else:
         le=0
      return render_template('practice.html',
         content={"theme":theme,
                  "level":le,
                  "card":cards.get_levels()[theme][int(le)][0],
                  "card_numbers":cards.get_levels()[theme]})
   else:
      return redirect('/')

@app.route('/practice/<theme>/<le>/next',methods=["POST"])
def practice_buttons(theme,le):
   if request.form.get('next'):
      deleted_card = cards.get_levels()[theme][int(le)][0]
      cards.del_card(deleted_card.card_id)
      cards.add_card(deleted_card)
      return redirect(url_for('practice',theme=theme,le=le))
   elif request.form.get('inc'):
      ccard = cards.get_levels()[theme][int(le)][0]
      if ccard.level < 3:
         ccard.level += 1
         cards.update_json()
   elif request.form.get('dec'):
      ccard = cards.get_levels()[theme][int(le)][0]
      if ccard.level > 1:
         ccard.level -= 1
         cards.update_json()
   elif request.form.get('del'):
      cards.del_card(cards.get_levels()[theme][int(le)][0].card_id)
      return redirect(url_for('practice',theme=theme,le=le))

   return redirect(url_for('practice',theme=theme,le=le))

@app.route('/practice/<theme>',methods=["POST"])
def level_choser(theme):
   level = request.form.get('level')
   return redirect(url_for('practice',theme=theme,le=level))

@app.route('/shutdown',methods=['GET'])
def shutdown():
   process_name = 'python.exe'
   result = os.system(f"taskkill /f /im {process_name}")

if __name__ == '__main__':
   app.run()