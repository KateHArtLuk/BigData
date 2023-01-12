# Поиск по вакансиям через API hh.ru
import requests
import json
from tqdm import tqdm
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np


def get_ids(progrs: tuple):
    ids = {}
    for prog in progrs:
        ids[prog] = []
        page = 0
        while True:
            req = requests.get(
                'https://api.hh.ru/vacancies',
                params={
                    'area': 113,
                    'text': prog,
                    'search_field': 'name',
                    'per_page': 100,
                    'page': page
                }
            )
            data = req.content.decode()
            req.close()
            data_dict = json.loads(data)
            ids[prog] += [item['id'] for item in data_dict['items']]
            if len(data_dict['items']) < 100:
                break
            page += 1
    return ids


def set_json(file_name: str, d: dict):
    with open(f'{file_name}.json', 'w', encoding='utf-8') as file:
        json.dump(d, file, indent=4, ensure_ascii=False)


def get_json(file_name):
    with open(f'{file_name}.json', 'r', encoding='utf-8') as file:
        res = json.load(file)
    return res


def set_csv(d):
    pd.DataFrame(d['data']).to_csv('out.csv', index=False, sep=';', encoding="utf-8-sig")


def get_data(d_ids, progrs):
    for prog, ids in d_ids.items():
        print(prog)
        if prog in progrs:
            result = []
            for vacancy_id in tqdm(ids):
                req = requests.get(
                    'https://api.hh.ru/vacancies/' + vacancy_id
                )
                data = req.content.decode()
                req.close()
                item = json.loads(data)
                result.append(item)
            res = {prog: result}
            set_json(prog, res)


def pars_json(file_names):
    for file_name in file_names:
        data = get_json(file_name)
        result = {}
        result[file_name] = []
        for req in data[file_name]:
            try:
                res = {}
                res['title'] = req['name']
                res['area'] = req['area']['name']
                if req['salary'] is None:
                    res['salary'] = 0
                else:
                    k = 1
                    if req['salary']['currency'] == 'USD':
                        k = 60
                    if req['salary']['to'] is not None:
                        res['salary'] = req['salary']['to'] * k
                    else:
                        res['salary'] = req['salary']['from'] * k
                res['experience'] = req['experience']['name']
                result[file_name].append(res)
            except Exception:
                print(file_name, res)
            finally:
                set_json(f'lite_{file_name}', result)


def files_to_dict(progs):
    res_d = {}
    res_d['data'] = []
    for prog in progs:
        old_d = get_json(f'lite_{prog}')

        for vac in old_d[prog]:
            vac['prog'] = prog
            res_d['data'].append(vac)
    return res_d


def get_df():
    data_url = 'out.csv'
    data = pd.read_csv(data_url, sep=';')
    print('Входные данные')
    print(data.prog.value_counts())
    data['stag'] = 'Other'
    data.loc[data.experience.str.contains('Нет опыта'), 'stag'] = 0
    data.loc[data.experience.str.contains('От 1 года до 3 лет'), 'stag'] = 1
    data.loc[data.experience.str.contains('От 3 до 6 лет'), 'stag'] = 2
    data.loc[data.experience.str.contains('Более 6 лет'), 'stag'] = 3
    data = data[['prog', 'stag', 'salary']].loc[data.area == 'Москва'].loc[data.salary > 0].reset_index()
    print('Вакансии по Мск и с указанной ЗП')
    print(data.prog.value_counts())
    r = pd.pivot_table(data,
                       index=["prog"],
                       values=["salary"],
                       columns=["stag"],
                       aggfunc=[np.mean],
                       fill_value=0)
    return r

def print_card(arr):
    fig, ax = plt.subplots(1, 1, figsize=(12, 24))

    # перебираем оба датасета по одному элементу
    # получаем значения минут и часов для разметки осей
    labels = arr.applymap(lambda v: str(v) if v == arr.values.max() else '')
    # формируем тепловую карту
    sns.heatmap(arr,
                cmap="RdPu",  # тема оформления
                annot=labels,  # разметку осей берём из переменной labels
                annot_kws={'fontsize': 14},  # размер шрифта для подписей
                fmt='',  # говорим, что с метками надо работать как со строками
                square=True,  # квадратные ячейки
                vmax=300000,  # максимальное
                vmin=0,  # и минимальное значение твитов в ячейке
                linewidth=0.02,  # добавляем разлиновку сеткой
                linecolor="#222",  # цвет сетки
                ax=ax,  # значение каждой клетки в тепловой карте берём в соответствии с датасетом
                )

    # сохраняем результат в файл final.png
    plt.tight_layout()
    plt.savefig('final.png', dpi=120)


if __name__ == "__main__":
    progrs = ('javascript', 'html', 'python', 'java', 'node.js', 'typescript', 'C#', 'C++')
    arr = get_df()
    print_card(arr)