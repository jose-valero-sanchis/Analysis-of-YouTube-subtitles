# -*- coding: utf-8 -*-

from main import *

if __name__ == '__main__':
    name_channel = '@TechWithTim'
    order_mode = 'Popular'
    n_videos = 10
    flag = 0
    lista_url = get_urls_channel(name_channel, n_videos, order_mode)   
    if lista_url is not None and len(lista_url) > 0:
        print('\nGenerating the summary...')
        lang_name, l_trans, l_problems = get_videos_transcription(lista_url)
        d_trans = get_dic_transcription(lang_name, l_trans)
        d_info = channel_info(lista_url)
        if order_mode == 'Recently uploaded':
            dates = list(d_info['date_count'].keys())
            n_vid = list(d_info['date_count'].values())        
            plt.plot(dates,n_vid)
            plt.gca().invert_xaxis()
            plt.rcParams["figure.figsize"] = [50, 3.50]
            plt.rcParams["figure.autolayout"] = True
            plt.savefig(f'{name_channel}.png', bbox_inches='tight')
        elif order_mode == 'Popular':
            flag = 1
            sorted_videos = sorted(d_info['date_count'].items(), key=lambda x:x[1], reverse=True)
            mas_pop = []
            i = 0
            for (u,v) in sorted_videos:
                try:
                    if i < 10:
                        mas_pop.append((u,v))
                        i += 1
                    else:
                        break
                except:
                    break
        
        d_trans_fil = {}
        for k, v in d_trans.items():
            if not k == '__' and not k.isnumeric():
                d_trans_fil[k] = v
        
        pal_mas = []
        i = 0
        for k,v in d_trans_fil.items():
            if i < 20:
                pal_mas.append((k,v))
                i += 1
            else:
                break
        
        keyList = d_trans_fil.keys()
        valueList = d_trans_fil.values()
        rows = zip(keyList, valueList)
        with open(f'{name_channel}_dictionary.csv', 'w', newline='', encoding="utf-16") as f:
            writer = csv.writer(f)
            for row in rows:
                writer.writerow(row)
        
        with open(f'{name_channel}_info.txt', 'w', encoding="utf-16") as f:
            f.write(f'Name channel: {name_channel}\n')
            f.write(f'\nNumber of videos considered: {len(l_trans)}.\n')
            f.write(f"\nTotal views: {d_info['views']}")
            f.write(f"\nAverage views: {d_info['avg_views']}\n")
            f.write(f"\nTotal length: {d_info['length']}")
            f.write(f"\nAverage length: {d_info['avg_length']}\n")
            if len(l_problems) == 0:
                f.write(f'\nBelow are the 20 most used words in the {len(l_trans)} videos without considering some stopwords.\n')
            else:
                f.write(f'\nBelow are the 20 most used words in the {len(l_trans) - len(l_problems)} videos considered (those for which the transcript is available)\n')
                f.write('without considering some stopwords.\n')
            f.write('\n')
            for e in pal_mas:
                f.write(f"{' '*2}{e[0]} --> {str(e[1])}\n")
            f.write('\nIf you want to see the complete list, you can get it in the cvs file located in the same location as this file.\n')
            if flag == 0:
                f.write('\nIn the same directory where this file is located you can find a png with a graph in which you can see the amount of videos uploaded in each month/year.')
            elif flag == 1:
                f.write("\nAs order_mode is 'Popular' it does not make sense to show a graph with the evolution of the videos.\n")
                f.write(f"However, below you can see in which month/year the most popular videos of {name_channel} were uploaded.\n")
                f.write('\n')
                for e in mas_pop:
                    f.write(f"{' '*2}{e[0]} --> {e[1]}\n")
            f.write('\n\n')
        
        print('\nSummary generated. Consult the directory where this file is located.')
        
        word = input(f'Enter the word on which you want to know the number of times\nit has been said in the {len(l_trans) - len(l_problems)} videos considered: ')
        while True:
            try:
                print(f'\nThe word "{word}" is repeated {d_trans_fil[word]} times')
            except:
                print(f'\nThe word "{word}" is not said at all in the {len(l_trans) - len(l_problems)} videos or is a stopword. ')
            
            other = input('Another one? (y/n): ')
            if other == 'y':
                word = input('Enter another word: ')
            else:
                break