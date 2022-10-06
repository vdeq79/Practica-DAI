from urllib import response
from flask import Flask, send_from_directory, render_template, Response, request, jsonify
from flask_restful import Resource, Api, reqparse
from bson import ObjectId
from bson.json_util import dumps
from pymongo import MongoClient
from math import isqrt
import random
import re
import json
# Conectar al servicio (docker) "mongo" en su puerto estandar
client = MongoClient("mongo", 27017) 

# Base de datos
db = client.cockteles   

app = Flask(__name__)

api = Api(app)
#<----------------------------------------------------------------------------------------------------------------------------------->
@app.route('/')
def hello_world():
  return 'Hello, World!'

#<----------------------------------------------------------------------------------------------------------------------------------->
@app.route('/criba/<int:n>')
def criba(n):
    list = [True] * (n-1)
    numeros = []

    for i in range(2,isqrt(n)+1):
        if list[i-2]:
            for j in range(i,int(n/i)+1):
                list[i*j-2] = False

    for i in range(0,len(list)):
      if list[i]:
        numeros.append(i+2)

    return numeros

#<----------------------------------------------------------------------------------------------------------------------------------->
@app.route('/fibonacci/<fichero>')
def fibonacci(fichero):

  def calculo(n):
    if(n==1):
        return 1
    elif(n==0):
        return 0
    else:
        return calculo(n-1)+calculo(n-2)


  f=open("./static/"+fichero,"r")
  n = int(f.read())
  f.close()
  fib = calculo(n)
  f = open("./static/salida.txt","w")
  f.write(str(fib))
  f.close()

  return "Se ha escrito en salida.txt"

#<----------------------------------------------------------------------------------------------------------------------------------->
@app.route('/balance')
def balance():
  letters = ['[',']']
  str = ''.join(random.choice(letters) for i in range(random.randrange(2,10,2)))

  if str[0]==']':
        return str+'<br/>False'

  sub = ''
  for i in range(0,len(str)):

      if len(sub)==0:
          sub+=str[i]
      elif sub[-1]=='[' and str[i]==']':
          sub = sub[:-1]
      else:
          sub+=str[i]

  if sub=='':
      return str+'<br/>True'
  else:
      return str+'<br/>False'

#<----------------------------------------------------------------------------------------------------------------------------------->
@app.route('/check1/<input>')
def check1(input):
  result = re.search(r'^[a-zA-Z0-9_]+\s[A-Z]\Z',input)
  if(result==None):
    return 'None'
  else:
    return str(result.group(0))
    
#<----------------------------------------------------------------------------------------------------------------------------------->
@app.route('/check2/<input>')
def check2(input):
  result = re.search(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}',input)
  if(result==None):
    return 'None'
  else:
    return str(result.group(0))

#<----------------------------------------------------------------------------------------------------------------------------------->
@app.route('/check3/<input>')
def check3(input):
    result = re.search(r'[0-9]{4}[\s-][0-9]{4}[\s-][0-9]{4}[\s-][0-9]{4}',input)
    if(result==None):
      return 'None'
    else:
      return str(result.group(0))

#<----------------------------------------------------------------------------------------------------------------------------------->
@app.route('/figuras')
def figuras():
    return render_template('figuras.html')

#<----------------------------------------------------------------------------------------------------------------------------------->
@app.errorhandler(404)
def page_not_found(error):
    return send_from_directory('static','page_not_found.html'), 404


#<----------------------------------------------------------------------------------------------------------------------------------->
def extraerDatosMongo(busqueda):

  lista_docs = []

  for doc in busqueda:
    app.logger.debug(doc)  # salida consola
    lista_docs.append(doc)

  response = {
  'len': len(lista_docs),
  'data': lista_docs
  }

  return dumps(response)

#<----------------------------------------------------------------------------------------------------------------------------------->
@app.route('/todas_las_recetas')
def mongo():
	# Encontramos los documentos de la coleccion "recipes"
  recetas = db.recipes.find() # devuelve un cursor(*), no una lista ni un iterador
  response = extraerDatosMongo(recetas)
  
  # Devolver en JSON al cliente
  return Response(response, mimetype='application/json')

#<----------------------------------------------------------------------------------------------------------------------------------->
@app.route('/recetas_de/<name>')
def recetas_de(name):

  recetas = db.recipes.find({"name":name})
  response = extraerDatosMongo(recetas)

  # Devolver en JSON al cliente
  return Response(response, mimetype='application/json')

#<----------------------------------------------------------------------------------------------------------------------------------->
@app.route('/recetas_con/<name>')
def recetas_con(name):

  recetas = db.recipes.find({"ingredients.name":name})
  response = extraerDatosMongo(recetas)

  # Devolver en JSON al cliente
  return Response(response, mimetype='application/json')

#<----------------------------------------------------------------------------------------------------------------------------------->
@app.route('/recetas_compuestas_de/<int:n>/ingredientes')
def compuestas_de_num(n):

  recetas = db.recipes.find({"ingredients":{"$size":n}})
  response = extraerDatosMongo(recetas)

  # Devolver en JSON al cliente
  return Response(response, mimetype='application/json')


#<----------------------------------------------------------------------------------------------------------------------------------->
@app.route('/recetas_compuestas_de/<path:varargs>')
def compuestas_de(varargs=None):
  varargs = varargs.split("/")

  #Eliminar las slashes vacías
  try:
    while True:
      varargs.remove("")
  except ValueError:
    pass

  recetas = db.recipes.find({"ingredients.name":{"$all":varargs}})
  response = extraerDatosMongo(recetas)

  # Devolver en JSON al cliente
  return Response(response, mimetype='application/json')
  #return varargs

#<----------------------------------------------------------------------------------------------------------------------------------->
# para devolver una lista (GET), o añadir (POST)
@app.route('/api/recipes', methods=['GET', 'POST'])
def api_1():
    if request.method == 'GET':
      lista = []
      buscados = db.recipes.find().sort('name')
      for recipe in buscados:
          recipe['_id'] = str(recipe['_id']) # paso a string
          lista.append(recipe)
      return jsonify(lista)
        
    if request.method == 'POST':
      data = request.get_json()
      result = db.recipes.insert_one(data)
      return str(result.inserted_id)

#<----------------------------------------------------------------------------------------------------------------------------------->
@app.route('/api/recipes/<id>', methods=['GET', 'PUT', 'DELETE'])
def api_2(id):
  if request.method == 'GET':
      buscado = db.recipes.find_one({'_id':ObjectId(id)})
      if buscado:
        buscado['_id'] = str(buscado['_id'])
        return jsonify(buscado)
      else:
        return jsonify({'error':'Not found'}), 404

  if request.method == 'PUT':
      data = request.get_json()
      result = db.recipes.update_one({'_id':ObjectId(id)}, data)

      if(result.matched_count==1):
        modificado = db.recipes.find_one({'_id':ObjectId(id)})
        modificado['_id'] = str(modificado['_id'])
        return jsonify(modificado)
      else:
        return jsonify({'error':'Not found'}), 404

  if request.method == 'DELETE':
      result = db.recipes.delete_one({'_id':ObjectId(id)})

      if(result.deleted_count==1):
          return id
      else:
        return jsonify({'error':'Not found'}), 404

#<----------------------------------------------------------------------------------------------------------------------------------->
recipe_parser = reqparse.RequestParser()
recipe_parser.add_argument("name", type=str, help="El nombre es requerido" ,required=True)
recipe_parser.add_argument("slug", type=str)
recipe_parser.add_argument("ingredients", action='append', help="La lista de ingredientes es requerida" ,required=True)
recipe_parser.add_argument("instructions", type=str, action='append' ,help="Las instrucciones son requeridas" ,required=True)


put_parser = reqparse.RequestParser()
put_parser.add_argument("$set", type=json ,help="El nombre es requerido" ,required=True)

#<----------------------------------------------------------------------------------------------------------------------------------->
# para devolver una lista (GET), o añadir (POST)
class RecipeList(Resource):
    def get(self):
        lista = []
        buscados = db.recipes.find().sort('name')
        for recipe in buscados:
            recipe['_id'] = str(recipe['_id']) # paso a string
            lista.append(recipe)
        return jsonify(lista)

    def post(self):
        args = recipe_parser.parse_args()
        result = db.recipes.insert_one(args)
        return str(result.inserted_id), 201


#<----------------------------------------------------------------------------------------------------------------------------------->
class Recipe(Resource):
    def get(self, id):
        buscado = db.recipes.find_one({'_id':ObjectId(id)})
        if buscado:
          buscado['_id'] = str(buscado['_id'])
          response = jsonify(buscado)
        else:
          response = jsonify({'error':'Not found'})
          response.status = 404
        
        return response

    def put(self, id):
        args = request.get_json()
        result = db.recipes.update_one({'_id':ObjectId(id)}, args)

        if(result.matched_count==1):
          modificado = db.recipes.find_one({'_id':ObjectId(id)})
          modificado['_id'] = str(modificado['_id'])
          response = jsonify(modificado)
          response.status = 201

        else:
          response = jsonify({'error':'Not found'})
          response.status = 404
        
        return response

    def delete(self, id):
        result = db.recipes.delete_one({'_id':ObjectId(id)})

        if(result.deleted_count==1):
          return id, 202
        else:
          response = jsonify({'error':'Not found'})
          response.status = 404
          return response


api.add_resource(RecipeList,'/RecipeList')
api.add_resource(Recipe,'/Recipe/<id>')


if __name__ == "__main__":
    app.run(debug=True)
