#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unicodedata
import tweepy
import json
import codecs
import os
import signal
import time
import random

import queue
import re
import math
from stopws import stopwords

consumer_key = 'd2lXdoAa1B1ts8pzEmTzrYym7'
consumer_secret = 'D1Z0LHL2jXpKQhOiwIpYGyXMAd0JPDRww6NJs8RWlQ7dn2gTCJ'
access_token = '192439126-3UyW8XPUL5mZbtjGnHGq20PLj1tiXcLoUssmdROx'
access_token_secret = 'JyDpIQEOMYOpHROdjo7FELFYpf39XcDBMDddtGZFi8NxX'

#autorizacion de api tweepy
def get_auth():
	auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
	auth.set_access_token(access_token, access_token_secret)
	return auth

#saca todas las tildes del texto
def elimina_tildes(s):
   return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))

#limpia la cadena de todo lo que no sea relevante
def limpiar_Contenido(cadena):
	cadena=elimina_tildes(cadena)
	#elimino los links
	patron=re.compile("\shttp\S+")
	cadena= patron.sub("",cadena)
	#elimino todo lo qe no es una letra
	patron=re.compile("[^(\w|\s)]")
	cadena= patron.sub("",cadena)

	#todas las palabras qedan separadas unicamente por espacios
	#elimino las stopwords
	for sw in stopwords:
		cadena=cadena.replace(' '+sw+' ',' ')
		cadena=cadena.replace(' '+sw+'\n','\n')
		cadena=cadena.replace('\n'+sw+' ','\n')
		cadena=cadena.replace(' '+sw.title()+' ',' ')
		cadena=cadena.replace(' '+sw.title()+'\n','\n')
		cadena=cadena.replace('\n'+sw.title()+' ','\n')

	cadena=cadena.replace("\n\n","\n")
	patronLetraAislada=re.compile(" \w ")
	cadena=patronLetraAislada.sub("",cadena)
		
	return cadena

#extrae terminos del documento data.txt
def BuscarTerminos():
	archivo = open("data.txt", "r")
	contenido = archivo.read()
	contenido= 	elimina_tildes(contenido)

	#Limpio el texto
	contenido=limpiar_Contenido(contenido)
	
	#separo todos espacios y armo un cjto de terminos
	terminosconrepeticiones=contenido.split()
	terminos=list(set(terminosconrepeticiones))

	nterm=len(terminos)
	print("\nCantidad de Terminos del Archivo: ",nterm)
		
	freq=[0 for j in range(nterm)]
	ruleta=[]
	TerminosConFreq=[]

	#creo la ruleta y unalista con terminos frequentes
	for t in range(0,nterm):
		freq[t]=contenido.count(terminos[t])
		#Priorizo las palabras que comienzan con mayusculas ya que deben ser nombre
		if(terminos[t].istitle()):	
			freq[t]=freq[t]*2
		if(freq[t]>1):		#descarto los que aparecen una sola vez
			TerminosConFreq.append((freq[t],terminos[t]))
			for probabilidad in range(freq[t]):
				ruleta.append(terminos[t])
		
	print("Cantidad de Dimensiones: ",len(TerminosConFreq))
	TerminosConFreq.sort(reverse=True)
	buscar=[]

	#tomo los 5 terminos mas importantes
	for i in range(5):
		buscar.append(TerminosConFreq[i][1])

	#tomo 10 terminos al azar de la ruleta sesgada, sin que se repitan
	for i in range(10):
		p=random.choice(ruleta)
		while(p  in buscar):
			p=random.choice(ruleta)
		buscar.append(p)
	
	consulta=""
	#tomo 5 frases formadas por 2 palabras de alta freq y 2 de baja freq al azar
	for i in range(5):
		consulta=random.choice(TerminosConFreq[0:10])[1]+" "
		consulta+=random.choice(TerminosConFreq[0:10])[1]+" "
		consulta+=random.choice(TerminosConFreq[0:10])[1]+" "
		consulta+=random.choice(TerminosConFreq[10:len(TerminosConFreq)])[1]+" "
		consulta+=random.choice(TerminosConFreq[10:len(TerminosConFreq)])[1]+" "
		buscar.append(consulta)
	
	return [buscar,TerminosConFreq]


#Busca tweets con los terminos terms y devuelve el contenido de los mismo, solo los diferentes 
def buscarTweets(terms):
	auth = get_auth()  # Retrieve an auth object using the function 'get_auth' above
	api = tweepy.API(auth)  # Build an API object.
	tweets=[]
	for termino in terms:
		tweetsTerm=api.search(termino,lang='es')
		j=5
		if len(tweetsTerm)<j:
			j=len(tweetsTerm)
		for i in range(j):
			tweets.append(tweetsTerm[i].text)
	return list(set(tweets))

#Selecciona delos tweets cuales tienen mayor parecido al contexto
def filtrarTweets(HP,tweets):
	ntweet=len(tweets)
	nterm =len(HP)
	similitud=[0 for j in range(ntweet)]
	Wq=[HP[i][0] for i in range(nterm)]
	terms=[HP[i][1] for i in range(nterm)]
	filtrados=[]	

	#similitud por 
	for i in range(ntweet):
		prodVect=0
		modDi=0
		modDk=0.00000001
		for j in range(len(terms)):
			Wik=limpiar_Contenido(tweets[i]).count(terms[j])
			if(terms[j].istitle()):
				Wik=Wik*2
			prodVect+=Wq[j]*Wik
			modDi+=(Wq[j]*Wq[j])
			modDk+=(Wik*Wik)
		similitud[i]=prodVect/(math.sqrt(modDi)*math.sqrt(modDk))
		filtrados.append((similitud[i],tweets[i]))

	filtrados.sort(reverse=True)
	i=0
	print('\n Tweets Recolectados: ')
	while(i<len(filtrados) and filtrados[i][0]>0.45):
		print(filtrados[i][0],'=',filtrados[i][1])
		i=i+1

if __name__ == '__main__':
	print('Busqueda Basada en Contexto')
	print('Analizando Terminos Relevantes...')
	[terminos,HP]=BuscarTerminos()
	print('\nSe recuperaron los',len(terminos),' terminos mas importantes\nson:',terminos)
	print('\nBuscando 100 Tweets...')
	tweets=buscarTweets(terminos)
	print('Se recuperaron ',len(tweets),'tweets distintos')
	print('Filtrando Tweets')
	filtrarTweets(HP,tweets)
	print('\nFinalizo Correctamente')

	

			





