# -*- coding: utf-8 -*-
'''
Created on Mon Dec 26 19:02:37 2022

@author: Jose
'''

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from nltk.corpus import stopwords
import datetime
import matplotlib.pyplot as plt
import re
from time import sleep # si se obtienen resultados inesperados, probar a aumentar los tiempos de espera
import numpy
import csv
from collections import Counter
import math

def check_exists_by_xpath(driver, xpath):
    try:
        driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True

def _open_youtube_channel(url):
    """
    _open_youtube_channel accede a un canal de YouTube, comprueba que tenga el canal exista y que tenga videos. 
    Si todo esto es así, devuelve el driver. Si no, se le indica al usuario.
    
    Si la url no lleva a un canal de YouTube, también se le indica al usuario.

    Parameters
    ----------
    url : str
        URL de un canal de YouTube.

    Returns
    -------
    driver : selenium.webdriver.chrome.webdriver.WebDriver
        Objeto sobre el cual se realiza el web scraping. 
        Se instala automáticamente la primera vez que se ejecuta el programa

    """
    
    if url.startswith('https://www.youtube.com/'):
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.maximize_window()
        driver.get(url)
        driver.find_element(By.XPATH, '/html/body/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/form[1]/div/div/button').click()
        try:
            driver.find_element(By.XPATH, "/html/head/title")
            print('\nThe channel does not exist.')
            return None
        except: 
            if driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-browse/div[3]/ytd-c4-tabbed-header-renderer/tp-yt-app-header-layout/div/tp-yt-app-header/div[2]/tp-yt-app-toolbar/div/div/tp-yt-paper-tabs/div/div/tp-yt-paper-tab[2]').text != 'VIDEOS':
                print('\nThe channel has no videos.')
                return None
            return driver
    else:
        print('\nThe entered url is not correct.')

def _aux_get_urls_channel(driver, name_channel, n_videos):
    """
    _aux_get_urls_channel obtiene los primeros n_videos del canal name_channel.
    
    Se contempla los siguientes casos:
        
        - Se solicitan menos videos de los que hay publicados en el canal.
          En ese caso, se devuelve una lista cuya longitud es la deseada.
        
        - Se soliciten más videos de los que hay publicados en el canal. 
          En ese caso, se devuelve una lista con las urls de todos los videos publicados 
          y se informa al usuario de la situación.

    Parameters
    ----------
    driver : selenium.webdriver.chrome.webdriver.WebDriver
        Objeto sobre el cual se realiza el web scraping.
    name_channel : str
        Nombre del canal (con el @).
    n_videos : int
        Número de urls que se desea obtener.

    Returns
    -------
    res : list
        Lista que contiene las urls solicitadas.
    
    """
    
    if n_videos > 1:
        res = []
        n_row = math.ceil(n_videos/4)
        for i in range(n_row):
            if i != 0 and i % 7 == 0: #Los videos se cargan en bloques de 7 filas. Para acceder a la 8ª, 16ª... hay que scrollear
                driver.execute_script(f'window.scrollTo(0, {500*(i+1)})') 
                sleep(0.5)
            
            for j in range(4):
                if i == 0 and j == 0:
                    driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-browse/ytd-two-column-browse-results-renderer/div[1]/ytd-rich-grid-renderer/div[6]/ytd-rich-grid-row[1]/div/ytd-rich-item-renderer[1]').click()
                    res.append(driver.current_url)
                    sleep(0.5)
                    driver.execute_script('window.history.go(-1)')
                
                else:
                    try:
                        enl = driver.find_element(By.XPATH, f'/html/body/ytd-app/div[1]/ytd-page-manager/ytd-browse/ytd-two-column-browse-results-renderer/div[1]/ytd-rich-grid-renderer/div[6]/ytd-rich-grid-row[{i+1}]/div/ytd-rich-item-renderer[{j+1}]/div/ytd-rich-grid-media/div[1]/ytd-thumbnail/a').get_attribute('href')
                        res.append(enl)
                        if len(res) == n_videos:
                            break
                    except:
                        print(f'\nThe channel {name_channel} has less than {n_videos} videos published. {len(res)} urls successfully obtained.')
                        return res
        
        if res[-1] == res[-2]: # por algun motivo en algunos canales con pocos videos, el último url sale duplicado
            res.pop(-1)
        
        print(f'\n{len(res)} urls successfully obtained.')   
        return res
    
    elif n_videos == 1:
        driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-browse/ytd-two-column-browse-results-renderer/div[1]/ytd-rich-grid-renderer/div[6]/ytd-rich-grid-row[1]/div/ytd-rich-item-renderer[1]').click()
        res = [driver.current_url]
        print(f'\n{len(res)} url successfully obtained.')
        return res

def get_urls_channel(name_channel, n_videos, order_mode='Recently uploaded'):
    """
     get_urls_channel tiene como objetivo preparar la llamada a _aux_get_urls_channel: 
        
        - Si el numero de videos solicitados es 0 se devuelve una lista vacia
          y si es un numero negativo se informa al usuario de que este numero ha de ser positivo.
          
        - Si order_mode es "Popular" y el canal tiene la opción de ordenar, se accede a
          la lista de videos ordenados por popularidad.
        
          Si order_mode es "Popular" pero el canal no tiene la opción de ordenar,
          se le indica al usuario de que la lista obtenida está ordenada por "Recently uploaded".
          
          Si se da un order_mode distinto a "Popular" o "Recently uploaded", se le indica que
          el modo de ordenacion no es correcto.
    
    Parameters
    ----------
    name_channel : str
        Nombre del canal (con el @).
    n_videos : int
        Número de urls que se desea obtener..
    order_mode : str, optional
        El valor por defecto es "Recently uploaded". Indica el modo de ordenación de los videos.
        Para que se ejecute, tiene tomar alguno de los siguientes valores:
            - "Recently uploaded". Obtiene las urls ordenadas por fecha de publicación de los videos 
              (de más nuevos a más antiguos) 
            - "Popular". Obtiene las urls ordenadas por la cantidad de visitas de los videos
    
    Returns
    -------
    res: list
        Lista que contiene las urls solicitadas.
    
    """
    if n_videos == 0:
        print('\nThe list obtained does not contain any url')
        return []
    if n_videos < 0:
        print('\nThe number of videos must be positive.')
        return
    
    res = []
    url = f'https://www.youtube.com/{name_channel}/videos'
    driver = _open_youtube_channel(url)
    if driver is not None:
        if order_mode == 'Popular':
            try:
                driver.find_element(By.XPATH, '/html/body/ytd-app/div[1]/ytd-page-manager/ytd-browse/ytd-two-column-browse-results-renderer/div[1]/ytd-rich-grid-renderer/div[1]/ytd-feed-filter-chip-bar-renderer/div/div[3]/iron-selector/yt-chip-cloud-chip-renderer[2]').click()
            except:
                print(f'\nThe {name_channel} channel does not have enough videos to be sorted by "Popularity". The list obtained is sorted by "Recently Uploaded".')
                res = _aux_get_urls_channel(driver, name_channel, n_videos)
                return res
        elif order_mode != 'Popular' and order_mode != 'Recently uploaded':
            print('\nOrder mode not valid.')
            return
    
        res = _aux_get_urls_channel(driver, name_channel, n_videos)
        return res

#----------------------------------------------------------------------------------------------

def get_video_transcription(id_video, lang):
    """
    get_video_transcription abtiene la transcripción de un video de youtube

    Parameters
    ----------
    id_video : str
        Identificador de un video. Por ejemplo, dada la siguiente 
        url https://www.youtube.com/watch?v=x22v39Cka1o el identificador 
        es x22v39Cka1o
    lang : list
        Lista de idiomas en los cuales puede estar el video.

    Returns
    -------
    l_cap : list
        Lista de diccionarios donde las claves son 'text' y 'start', y los
        valores son una parte de la transcripción y cuando empieza dicha parte.

    """
    l_cap = YouTubeTranscriptApi.get_transcript(id_video, languages=lang)
    for d in l_cap:
        del d['duration']
    return l_cap

def get_videos_transcription(l):
    """
    get_videos_transcription obtiene una lista de listas de transcripciones

    Parameters
    ----------
    l : list
        Lista de las urls de los videos de los cuales se quiere obtener la
        transcripcion.

    Returns
    -------
    lang_name : str
        Idioma más frecuente en el cual están los videos de la lista. 
        Si este no se reconoce como idioma, por ejemplo es-ES, se devuelve
        el segundo idioma más frecuente
    res : list
        Lista que contiene listas donde se encuentra la transcripción
        de cada video.
    """
    
    res = []
    problems = []
    l_lang = []
    n_videos = 0
    for url in l:
        aux = []
        try:
            id_video = url.replace('https://www.youtube.com/watch?v=', '')
            transcript_list = YouTubeTranscriptApi.list_transcripts(id_video)
            l_lang_aux = []
            for t in transcript_list:
                l_lang_aux.append(re.findall(r'(\A\D{0,7})\s+', str(t))[0])
            l_cap = get_video_transcription(id_video, l_lang_aux)
            n_videos += 1
            for d in l_cap:
                aux.append(d['text'])
            
            for e in l_lang_aux:
                l_lang.append(e)
            l_lang_aux = []
        except:
            problems.append(url.replace('https://www.youtube.com/watch?v=', ''))

        res.append(aux)    
        
    arr = numpy.array(l_lang)
    try:
        ctr = Counter(arr.ravel())
        most_common_value, its_frequency = ctr.most_common(2)[0]
        lang_name = get_lenguage_from_code(most_common_value)
    except:
        ctr = Counter(arr.ravel())
        second_most_common_value, its_frequency = ctr.most_common(2)[1]
        lang_name = get_lenguage_from_code(second_most_common_value)
                     
    if n_videos != len(l):
        print(f"""\nThere have been problems obtaining a transcript of the following videos: {', '.join(map(str, problems))}.""")
        print(f"""This may be due to subtitles not being available. Consequently, of the {len(l)} videos only the transcription of {n_videos} has been obtained.""")
    return lang_name, res, problems

def get_video_info(url):
    """
    get_video_info obtiene la cantidad de likes y visistas, la longitud y la
    fecha de publicación de un video

    Parameters
    ----------
    url : str
        URL del video del cual se desea obtener los datos.

    Returns
    -------
    d_info : dict
        Diccionario en el cual las claves son 'views', 'length' y 'date',
        y los valores son los respectivos datos.
    """
    video = YouTube(url)
    views = int(video.views)
    length = int(video.length)
    date = video.publish_date
    d_info = {'views': views, 'length': length, 'date': date}
    return d_info

def get_lenguage_from_code(code):
    """
    get_lenguage_from_code crea un diccionario donde las claves son los códigos
    de los idiomas y los valores los nombres de dichos idiomas. Una vez creado
    obtiene el nombre del idioma a partir del codigo dado
    Por ejemplo, dado 'es' devuelve 'spanish'

    Parameters
    ----------
    code : str
        Codigo de un idioma.

    Returns
    -------
    Idioma obtenido a partir buscar el código en el diccionario obtenido.

    """
    dic = {}
    result = requests.get("https://meta.wikimedia.org/wiki/Template:List_of_language_names_ordered_by_code")
    html_doc = result.content
    soup = BeautifulSoup(html_doc, "lxml")
    tabla = soup.find('tbody')
    filas = tabla.find_all('tr')
    for fila in filas:
        col = fila.find_all('td')   
        if len(col) > 0:
            dic[col[0].text.replace('\n', '')] = col[1].text.lower().replace('\n', '')
    return dic[code]

#-----------------------------------------------------------------------------

def get_dic_transcription(lang_name, l_trans):
    """
    get_dic_transcription obtiene un diccionario con las palabras más utilizadas.
    Además quita algunas stopwords que genera a partir de lang_name

    Parameters
    ----------
    lang_name : str
        Nombre (no codigo) del idioma en el cual están escritos (mayoritariamente)
        los textos de l_trans.
    l_trans : list
        Lista de listas que contienen la transcripción de un video.

    Returns
    -------
    sort_dict : dict
        Diccionario donde las claves son la palabras y los valores la frecuencia
        con la que aparecen en total (en los textos de todas las listas).

    """
    
    dic_cap = {}
    if len(l_trans) > 0:
        try:
            stop_words = stopwords.words(lang_name)
            if lang_name == 'spanish':
                new_stopwords = ['si', 'pues', 'entonces', 'bueno', 'así', 'ver', 'ser', 'aquí', 'ahora', 'hacer', 'personas', 'dijo', 'dice', 
                                 'cosas', 'va', 'cómo', 'sé', 'bien', 'puede', 'día', 'euros', 'vamos', 'hace', 'después', 'decir', 'mismo', 
                                 'dentro', 'claro', 'voy', 'saber', 'vez', 'cada', 'días', 'ahí', 'nadie', 'dicho', 'hoy', 'momento', 'hecho',
                                 'hablar', 'quiero', 'haciendo', 'luego', 'visto', 'música']
                stop_words.extend(new_stopwords)
            elif lang_name == 'english':
                new_stopwords = ['going', 'say', 'let', 'like', 'want', 'go', 'right', 'actually', 'need', 'get', 'one', 
                                 'something', 'gonna', 'okay', 'see', 'know', 'make', 'thing', 'music']
                stop_words.extend(new_stopwords)
            
            for lista in l_trans:
                for frase in lista:
                    l_pal = re.findall(r'\w+', frase)
                    for pal in l_pal:
                        pal = pal.lower()
                        if pal not in stop_words and pal not in dic_cap:
                            dic_cap[pal] = 1
                        elif pal not in stop_words and pal in dic_cap:
                            dic_cap[pal] += 1
        except:
            for lista in l_trans:
                for frase in lista:
                    l_pal = re.findall(r'\w+', frase)
                    for pal in l_pal:
                        pal = pal.lower()
                        if pal not in dic_cap:
                            dic_cap[pal] = 1
                        elif pal in dic_cap:
                            dic_cap[pal] += 1
            
    sort_dict = {k: v for k, v in sorted(dic_cap.items(), key=lambda item: item[1], reverse=True)}
    return sort_dict
    
def channel_info(lista_url):
    """
    channel_info obtiene información de un canal a partir de los videos que 
    se pasan en el parametro. Esta función calcula el numero de visitas totales 
    y medios, la longitud total y media, así como un diccionarios en el cual
    las claves son los meses y años en los que se subieron los videos de la lista
    y los valores la cantidad de videos que se subieron en ese mes/año

    Parameters
    ----------
    lista_url : list
        Lista de urls (la idea es que todas las urls sean de un mismo canal).

    Returns
    -------
    d_info : dict
        Diccionario que contiene toda la información comentada anteriomente.

    """
    d_info = {}
    for url in lista_url:
        d_info_aux = get_video_info(url)
        for k,v in d_info_aux.items():
            if k != 'date':
                if k not in d_info:
                    d_info[k] = v
                else:
                    d_info[k] += v
            else:
                if k not in d_info:
                    d_info[k] = [v]
                else:
                    d_info[k].append(v)
    
    d_info['n_videos'] = len(lista_url)
    
    d_info['avg_views'] = d_info['views']/d_info['n_videos']
    d_info['avg_length'] = datetime.timedelta(seconds=int(d_info['length']/d_info['n_videos']))
    d_info['length'] = datetime.timedelta(seconds = d_info['length'])

    date_dic = {}
    for date in d_info['date']:
        d = str(date.year) + '-' + str(date.month)
        if d not in date_dic:
            date_dic[d] = 1
        else:
            date_dic[d] += 1
    d_info['date_count'] = date_dic
    del d_info['date']
    
    return d_info
