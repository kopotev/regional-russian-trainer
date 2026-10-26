#!/usr/bin/env python3
"""Build the single public final data file from the accepted 94-word screen.

Original count responses stay in the research archive, outside the public release.
No network calls; examples below are editorial learning examples, not quotations.
"""
import csv, hashlib, json, re, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / 'research/RUN-2026-10-24-KZ-SCREEN-01'
SOURCE = STUDY / 'processed/Kazakhstan_frequency_screen_passed.csv'

# lemma | Russian teaching definition | English gloss | constructed Russian example
TEXT = r'''
женгешка|Разговорное название женге — жены старшего брата; употребление и оттенок обращения зависят от отношений между людьми.|Informal term related to zhenge, an elder brother's wife; its tone depends on the relationship.|В рассказе о семье слово «женгешка» обозначает жену старшего брата.
енпф|Сокращённое название Единого накопительного пенсионного фонда Казахстана; обычно пишется прописными буквами: ЕНПФ.|ENPF: Kazakhstan's Unified Accumulative Pension Fund; normally written in capitals.|В выписке ЕНПФ указаны пенсионные накопления.
саумал|Свежее, ещё не сквашенное кобылье молоко; его следует отличать от кумыса.|Fresh, unfermented mare's milk, distinct from fermented kumys.|В описании продукта саумал отличают от кумыса.
жырау|Поэт-сказитель в казахской традиции, исполняющий поэтические произведения.|A poet and oral performer in the Kazakh tradition.|Жырау исполнил произведение перед слушателями.
кызылординский|Связанный с Кызылордой или Кызылординской областью; конкретную отнесённость показывает контекст.|Relating to Kyzylorda or Kyzylorda Region; the context identifies which.|Кызылординский музей подготовил выставку.
тиын|Сотая доля тенге; название денежной единицы не означает, что соответствующая монета находится в обращении.|One hundredth of a tenge; the unit name does not establish that a coin is in circulation.|Один тенге равен ста тиынам.
шымкентский|Связанный с городом Шымкентом.|Relating to the city of Shymkent.|Шымкентский театр приехал на гастроли.
акимат|Местный орган исполнительной власти в Казахстане; учреждение, а не отдельный руководитель.|A local executive authority in Kazakhstan, rather than its individual head.|Жители направили обращение в акимат.
маслихат|Местный представительный орган в Казахстане; его следует отличать от исполнительного органа — акимата.|A local representative body in Kazakhstan, distinct from the executive akimat.|На заседании маслихата обсудили местный бюджет.
мажилис|Название нижней палаты Парламента Казахстана; в названии учреждения обычно пишется «Мажилис».|The name of the lower chamber of Kazakhstan's Parliament.|Депутаты Мажилиса обсудили законопроект.
грантник|Разговорное название человека, обучающегося по образовательному гранту; не название отдельной профессии.|An informal term for a student studying under an educational grant.|Грантник рассказал, как поступал в университет.
тенге|Национальная денежная единица Казахстана.|Kazakhstan's national currency, the tenge.|Билет стоит две тысячи тенге.
шанырак|Круглый верхний элемент каркаса юрты; в символическом употреблении может обозначать дом и семью.|The circular crown of a yurt's frame; also a symbol of home and family.|Через шанырак в юрту проникает свет.
мангистауский|Связанный с Мангистау или Мангистауской областью.|Relating to Mangystau or Mangystau Region.|Мангистауский пейзаж запомнился путешественникам.
костанайский|Связанный с Костанаем или Костанайской областью.|Relating to Kostanay or Kostanay Region.|Костанайский университет организовал встречу.
саукеле|Традиционный высокий головной убор казахской невесты.|A traditional tall Kazakh bridal headdress.|В музее показали украшенный саукеле.
текемет|Традиционный узорный войлочный ковёр.|A traditional patterned felt carpet.|На выставке лежал узорный текемет.
иримшик|Казахское название творожного молочного продукта; способы приготовления и разновидности различаются.|A Kazakh curd-based dairy product, with different varieties and methods of preparation.|К чаю подали иримшик.
алматинский|Связанный с Алматы или Алматинской областью; точное значение определяется контекстом.|Relating to Almaty or Almaty Region, depending on context.|Алматинский театр объявил новый сезон.
акмолинский|Связанный с Акмолинской областью или с историческим названием Акмолинск; значение уточняется по контексту.|Relating to Akmola Region or the historical name Akmolinsk, depending on context.|В тексте описан акмолинский населённый пункт.
куырдак|Горячее блюдо из обжаренного мяса и/или субпродуктов; состав зависит от рецепта.|A hot dish of fried meat and/or offal; recipes vary.|На обед приготовили куырдак.
кокпар|Традиционная конная командная игра с борьбой за тушу козла или её спортивный заменитель.|A traditional equestrian team game involving a goat carcass or a sporting substitute.|Команда участвовала в соревнованиях по кокпару.
айтыс|Поэтическое состязание, обычно в форме импровизированного диалога акынов.|A poetic contest, commonly an improvised dialogue between akyns.|Два акына встретились на айтысе.
кюйши|Исполнитель кюев — инструментальных музыкальных произведений.|A performer of kuys, traditional instrumental compositions.|Кюйши исполнил произведение на домбре.
павлодарский|Связанный с Павлодаром или Павлодарской областью.|Relating to Pavlodar or Pavlodar Region.|Павлодарский коллектив выступил на фестивале.
тобет|Название казахской пастушьей сторожевой собаки; не любая собака вообще.|The name of a Kazakh livestock-guardian dog.|Тобет охранял стадо.
астанинский|Связанный с городом Астаной.|Relating to the city of Astana.|Астанинский музей открыл выставку.
оралман|Прежнее официальное обозначение этнического казаха, переселившегося в Казахстан; в современной официальной терминологии заменено словом «кандас».|A former official term for an ethnic Kazakh repatriate to Kazakhstan, replaced in official terminology by kandas.|В историческом документе употреблено слово «оралман»; современный термин нужно проверить отдельно.
карагандинский|Связанный с Карагандой или Карагандинской областью.|Relating to Karaganda or Karaganda Region.|Карагандинский музей подготовил экскурсию.
шубат|Кисломолочный напиток из верблюжьего молока.|A fermented camel's-milk drink.|Гостям предложили шубат.
кобыз|Традиционный смычковый струнный музыкальный инструмент.|A traditional bowed string instrument, the kobyz.|Музыкант играл на кобызе.
корпе|Стёганое одеяло или мягкая подстилка для сидения; конкретное назначение показывает контекст.|A quilt or padded cover used for bedding or seating, depending on context.|Для гостей разложили мягкие корпе.
казахоязычный|Говорящий, пишущий или представленный на казахском языке.|Kazakh-speaking or Kazakh-language.|Она читает казахоязычную газету.
асык|Небольшая кость надкопытного сустава овцы или другого животного, используемая в традиционных играх.|An animal knucklebone, commonly a sheep's, used in traditional games.|Дети играли в асыки.
жент|Сладкое блюдо на основе измельчённого зерна с жиром и сахаром; рецепты различаются.|A sweet dish based on crushed grain, fat and sugar; recipes vary.|К чаю подали жент.
актюбинский|Связанный с Актобе, прежним названием Актюбинск или Актюбинской областью.|Relating to Aktobe, its former name Aktyubinsk, or Aktobe Region.|Актюбинский коллектив приехал на конкурс.
казахстанский|Связанный с Казахстаном как страной; не обязательно связанный именно с казахским языком или этнической принадлежностью.|Relating to Kazakhstan as a country, without necessarily indicating Kazakh ethnicity or language.|Казахстанский университет принимает иностранных студентов.
ент|Единое национальное тестирование — название системы экзаменационного тестирования в Казахстане; обычно пишется «ЕНТ».|ENT: Unified National Testing in Kazakhstan; normally written in capitals.|Абитуриент готовится к ЕНТ.
байга|Традиционное конное состязание, скачки.|A traditional horse race or equestrian contest.|В программе праздника была байга.
кюй|Инструментальная музыкальная пьеса в казахской и родственных музыкальных традициях.|A traditional instrumental musical composition, a kuy.|На концерте прозвучал кюй.
бесбармак|Вариант названия блюда из варёного мяса и отварного теста, также называемого «бешбармак».|A spelling variant of beshbarmak, a dish of boiled meat and dough.|Хозяева приготовили бесбармак.
аким|Руководитель местного исполнительного органа в Казахстане; должностное лицо, а не учреждение.|The head of a local executive authority in Kazakhstan.|Аким встретился с жителями района.
дастархан|Накрытый стол с угощением; также связанная с ним традиция гостеприимства.|A table laid with food and, by extension, the associated tradition of hospitality.|Для гостей накрыли дастархан.
казахский|Связанный с казахским народом, казахским языком или культурой.|Relating to the Kazakh people, language or culture.|В школе изучают казахский язык.
мрп|Месячный расчётный показатель — расчётная величина, применяемая в Казахстане; её размер зависит от года.|MRP: the monthly calculation index used in Kazakhstan; its monetary value varies by year.|В документе сумма указана в МРП, поэтому важно знать год расчёта.
баурсак|Небольшое обжаренное изделие из теста; чаще употребляется форма множественного числа «баурсаки».|A small piece of fried dough, commonly served as baursaks.|К чаю принесли свежие баурсаки.
домбра|Казахский щипковый струнный музыкальный инструмент с длинным грифом.|A Kazakh plucked string instrument with a long neck.|Она учится играть на домбре.
акын|Поэт и певец-импровизатор в казахской и некоторых других центральноазиатских традициях.|A poet and improvising singer in Kazakh and other Central Asian traditions.|Акын исполнил новую песню.
трёхъязычный|Использующий три языка или представленный на трёх языках.|Using or presented in three languages.|На стенде размещён трёхъязычный текст.
семипалатинский|Связанный с Семипалатинском — историческим названием города Семей, либо с объектом, сохранившим это название.|Relating to Semipalatinsk, the historical name of Semey, or to a named site retaining it.|В статье обсуждается Семипалатинский полигон.
батыр|Богатырь, отважный воин; историко-культурное название.|A heroic or brave warrior, a historical and cultural term.|В легенде рассказывается о подвиге батыра.
чапан|Традиционная длинная верхняя одежда типа халата.|A traditional long robe or coat.|Почётному гостю подарили чапан.
иин|Индивидуальный идентификационный номер в Казахстане; обычно пишется «ИИН».|IIN: an individual identification number in Kazakhstan; normally written in capitals.|В форме есть поле для ИИН.
арык|Небольшой открытый канал для отвода или подачи воды, в том числе для орошения.|A small open water channel, including an irrigation ditch.|Вода текла по арыку.
бешбармак|Блюдо из варёного мяса и отварного теста; встречается также написание «бесбармак».|A dish of boiled meat and dough, also spelt besbarmak in Russian.|Гости попробовали бешбармак.
казы|Традиционное мясное изделие из конины, обычно в кишечной оболочке.|A traditional horse-meat preparation, commonly stuffed in a casing.|На блюде лежали нарезанные казы.
оси|В административном контексте Казахстана: объединение собственников имущества; сокращение обычно пишется «ОСИ».|OSI: a property owners' association in Kazakhstan; the abbreviation is normally capitalised.|Жильцы обсудили работу ОСИ.
аул|Сельское поселение; в Казахстане слово употребляется применительно к селу.|A rural settlement or village, including in Kazakhstan.|Летом семья приехала в аул.
докторантура|Ступень или программа подготовки к получению докторской степени; её устройство зависит от образовательной системы.|Doctoral education or a doctoral programme; arrangements depend on the education system.|После магистратуры она поступила в докторантуру.
докторант|Человек, обучающийся в докторантуре или проходящий подготовку к докторской степени.|A doctoral student or candidate.|Докторант представил результаты исследования.
самса|Выпечка с начинкой, часто мясной; варианты формы и рецепта различаются.|A filled baked pastry, often containing meat; varieties differ.|В пекарне продавалась горячая самса.
лагман|Блюдо с лапшой и подливой из мяса и овощей; состав зависит от рецепта.|A noodle dish with meat-and-vegetable sauce; recipes vary.|На обед заказали лагман.
тамга|Родовой, владельческий или иной условный знак в тюркских и других традициях.|A clan, ownership or other identifying mark in Turkic and other traditions.|На музейном предмете сохранилась тамга.
аксакал|Уважаемый пожилой мужчина, старейшина в ряде центральноазиатских и других традиций.|A respected elder in Central Asian and other traditions.|За советом обратились к аксакалу.
туркестанский|Связанный с городом Туркестаном, Туркестанской областью или историческим регионом Туркестан; значение зависит от контекста.|Relating to Turkistan city or region, or to historical Turkestan, depending on context.|В тексте описан туркестанский памятник архитектуры.
кумыс|Кисломолочный напиток из кобыльего молока; в отличие от саумала, проходит брожение.|A fermented mare's-milk drink, unlike unfermented saumal.|После обеда гостям предложили кумыс.
манты|Блюдо из теста с начинкой, приготовленное на пару; начинка может быть разной.|Steamed filled dumplings; fillings vary.|На ужин приготовили манты.
айран|Кисломолочный напиток, разновидности которого различаются по составу и густоте.|A fermented dairy drink with regional variations in ingredients and consistency.|К еде подали охлаждённый айран.
юрта|Традиционное сборно-разборное каркасное жилище кочевого быта.|A traditional portable framed dwelling associated with nomadic life.|Для выставки собрали юрту.
бата|Благословение, доброе напутствие в традиционном общении.|A blessing or good wishes expressed in a traditional social setting.|Перед дорогой старший произнёс бата.
базар|Рынок или торговое место; в разговорной речи возможны другие значения, которые требуют контекста.|A market or trading place; other colloquial senses require context.|На базаре купили фрукты.
кондоминиум|Форма совместного владения общим имуществом при индивидуальной собственности на отдельные помещения.|An ownership arrangement combining individual premises and shared common property.|Крыша относится к общему имуществу объекта кондоминиума.
кочевой|Связанный с образом жизни, предполагающим перемещение между местами проживания или выпаса.|Nomadic; relating to a way of life involving movement between dwelling or grazing sites.|На выставке рассказали о кочевом быте.
той|Праздник, торжество или праздничное собрание; вид события уточняется по контексту.|A celebration or festive gathering; the event type depends on context.|Родные собрались на той.
талкан|Продукт из обжаренного и размолотого зерна; состав и использование различаются.|A food made from roasted ground grain; ingredients and uses vary.|Для блюда использовали талкан.
они|Личное местоимение третьего лица множественного числа; в обычном употреблении заменяет названия нескольких людей или предметов.|The third-person plural personal pronoun, they.|Студенты пришли в музей. Они осмотрели выставку.
медресе|Мусульманское учебное заведение.|A Muslim educational institution, a madrasa.|В историческом здании раньше находилось медресе.
колледж|Учебное заведение; уровень и программа обучения определяются образовательной системой страны.|A college; its educational level and programme depend on the country's system.|После школы он поступил в колледж.
республиканский|Относящийся к республике либо имеющий охват всей республики; значение определяется контекстом.|Relating to a republic or covering the whole republic, depending on context.|Команда победила в республиканском конкурсе.
братишка|Разговорное уменьшительное к слову «брат»; также дружеское обращение, значение которого зависит от ситуации.|An informal diminutive of brother, also used as a familiar address.|Младший братишка пришёл со школы.
межэтнический|Относящийся к отношениям или взаимодействию между этническими группами.|Interethnic; involving relations between ethnic groups.|Участники обсудили межэтническое общение.
грант|Средства или поддержка, предоставленные для определённой цели; образовательный грант относится к обучению.|Funding or support awarded for a specified purpose, including study.|Студент получил образовательный грант.
камзол|Предмет одежды типа жилета или безрукавки; в описании казахского костюма — традиционная одежда соответствующего типа.|A waistcoat-like garment; in Kazakh dress, a traditional garment of that type.|В музее показали вышитый камзол.
она|Личное местоимение третьего лица единственного числа женского рода.|The feminine third-person singular personal pronoun, she or it.|Книга лежит на столе. Она открыта.
каймак|Густой молочный продукт, близкий к сливкам или сметане; приготовление и консистенция различаются.|A thick dairy product resembling cream; preparation and consistency vary.|К лепёшкам подали каймак.
горнодобывающий|Связанный с добычей полезных ископаемых.|Relating to the mining of mineral resources.|В регионе работает горнодобывающее предприятие.
пенсионка|Разговорное обозначение, связанное с пенсией, пенсионными взносами или накоплениями; точное значение устанавливается по контексту.|A colloquial expression connected with pensions, contributions or savings; the exact sense requires context.|В разговоре прозвучало слово «пенсионка»; собеседник уточнил, о каких взносах идёт речь.
тот|Указательное местоимение: обозначает уже названный или более удалённый предмет, человека либо ситуацию.|A demonstrative pronoun: that or the one, referring to something identified or more distant.|Этот дом новый, а тот построили раньше.
сват|Отец одного из супругов по отношению к родителям другого; также человек, участвующий в сватовстве.|A parent of one spouse in relation to the other spouse's parents; also a matchmaker.|Родители жениха и невесты познакомились как сваты.
тюбетейка|Небольшой круглый головной убор, распространённый у разных народов.|A small round cap worn in several cultural traditions.|На витрине лежала вышитая тюбетейка.
степной|Относящийся к степи — открытому равнинному пространству с преимущественно травянистой растительностью.|Relating to the steppe, an open, predominantly grassy plain.|Вдали виднелся степной пейзаж.
магистратура|Программа или ступень высшего образования, ведущая к степени магистра.|A master's degree programme or level of higher education.|После бакалавриата она выбрала магистратуру.
что|Местоименное слово, в вопросе указывающее на неизвестный предмет или содержание; также может служить союзом.|A pronominal word meaning what in questions; it can also function as a conjunction.|Что вы хотите узнать о новом слове?
весь|Определительное местоимение со значением полного охвата предмета, совокупности или времени.|A universal or totality pronoun meaning all, the whole or entire.|Весь день студенты готовились к выступлению.
'''

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-only',action='store_true',help='Validate the released final JSON without rebuilding it.')
    parser.add_argument('--source',type=Path,help='Optional original screened CSV; normally validate the published final JSON instead.')
    args=parser.parse_args()
    final_path=ROOT/'data/Kazakhstan_final.json'
    if args.validate_only or (args.source is None and not SOURCE.exists()):
        data=json.loads(final_path.read_text())
        words=data['words']
        assert len(words)==94 and len({w['lemma'] for w in words})==94
        assert len(data['legacy_cards'])==40
        for w in words:
            f=w['frequency']
            assert f['kz_hits']>=20 and f['kz_texts']>=10 and f['ratio_kz_ru']>=2
            assert abs(f['kz_ipm']-f['kz_hits']/f['kz_words']*1e6)<1e-8
            assert abs(f['ru_ipm']-f['ru_hits']/f['ru_words']*1e6)<1e-8
            assert w['definition']['ru'] and w['definition']['en'] and w['exercises']['recall']['answer']==w['lemma']
        print(json.dumps({'validated':str(final_path),'words':len(words),'legacy_cards':len(data['legacy_cards'])}))
        return
    source_file=args.source or SOURCE
    entries = {}
    for line in TEXT.strip().splitlines():
        lemma, ru, en, example = line.split('|')
        assert lemma not in entries
        entries[lemma] = (ru,en,example)
    rows=list(csv.DictReader(source_file.open(encoding='utf-8-sig')))
    assert len(rows)==94 and len({r['lemma'] for r in rows})==94
    assert set(entries)=={r['lemma'] for r in rows}, (set(entries)-{r['lemma'] for r in rows}, {r['lemma'] for r in rows}-set(entries))
    html=(ROOT/'inputs/Kazakhstan_lexicon_trainer.html').read_text()
    old=json.loads(re.search(r'<script type="application/json" id="dataset">(.*?)</script>',html,re.S).group(1))
    original={}
    for pack in old['packs']:
        for card in pack.get('cards',[]): original.setdefault(card['lemma'],[]).append(card)
    special={'они','она','что','тот','весь'}
    abbreviations={'енпф','ент','мрп','иин','оси'}
    geo={'кызылординский','шымкентский','мангистауский','костанайский','алматинский','акмолинский','павлодарский','астанинский','карагандинский','актюбинский','казахстанский','семипалатинский','туркестанский'}
    common={'докторантура','докторант','колледж','грант','магистратура','республиканский','межэтнический','горнодобывающий','степной','кочевой','трёхъязычный','братишка','сват','базар','кондоминиум'}
    fresh_sources={
      'оси':[{'title':'Что такое объединение собственников имущества (ОСИ) — gov.kz','url':'https://www.gov.kz/situations/342/intro?lang=ru','verification':'opened_2026-10-26'}],
      'оралман':[{'title':'Присвоение или продление статуса «Қандас» — gov.kz','url':'https://www.gov.kz/org/vko-altai/press/news/details/258642','verification':'opened_2026-10-26'}],
      'енпф':[{'title':'Пенсионная система — ЕНПФ','url':'https://www.enpf.kz/ru/financial-literacy/pensionsystem/48133/','verification':'opened_2026-10-26'}],
      'женгешка':[{'title':'Казахско-русский словарь: жеңге (основа разговорной формы)','url':'https://speak.tatar/ru/dict/kaz-rus/jenge-i/','verification':'dictionary_base_only_not_regional_distribution'}]
    }
    words=[]
    for i,r in enumerate(rows,1):
        lemma=r['lemma'];ru,en,example=entries[lemma]
        nums={k:int(r[k]) for k in ('kz_hits','kz_texts','kz_words','ru_hits','ru_texts','ru_words')}
        nums.update({k:float(r[k]) for k in ('kz_ipm','ru_ipm','ratio_kz_ru')})
        assert nums['kz_hits']>=20 and nums['kz_texts']>=10 and nums['ratio_kz_ru']>=2
        originals=original.get(lemma,[])
        sources=[]
        for c in originals:
            for source in c.get('sources',[]):
                item=dict(source);item['verification']='preserved_from_original_trainer_not_newly_reverified'
                if item not in sources:sources.append(item)
        sources.extend(fresh_sources.get(lemma,[]))
        category='annotation' if lemma in special else 'geography' if lemma in geo else 'institution' if lemma in abbreviations else 'general' if lemma in common else 'culture'
        teaching_pos={'они':'personal_pronoun_plural','она':'personal_pronoun_feminine','что':'pronominal_word_or_conjunction','тот':'demonstrative_pronoun','весь':'totality_pronoun'}.get(lemma,'adjective' if r['pos']=='A' else 'noun')
        nr='Частотный отбор не устанавливает особого регионального значения. Учебный пример составлен редактором и не является корпусной цитатой.'
        ne='Frequency screening does not establish a distinct regional meaning. The learning example is editorial, not a corpus quotation.'
        if lemma in special:
            nr+=' В запросе сохранена автоматическая категория '+r['pos']+'; её совпадения не доказывают, что это обычное употребление существительного или прилагательного. Карточка учит анализу разметки.'
            ne+=' The counted query category '+r['pos']+' is retained; these matches do not establish ordinary noun or adjective use. This card teaches annotation literacy.'
        if lemma in {'пенсионка','женгешка'}:
            nr+=' Разговорная форма: не переносите это объяснение на каждый случай без проверки контекста.'
            ne+=' Colloquial form: do not apply this explanation to every occurrence without checking context.'
        if lemma=='оралман':
            nr+=' Исторический термин: в современной официальной речи используйте актуальное наименование «кандас»; карточка не является правовой консультацией.'
            ne+=' Historical term: contemporary official usage uses kandas; this card is not legal advice.'
        if lemma in abbreviations:
            nr+=' Строчная форма — точная лемма корпусного запроса; обычное написание сокращения — прописными буквами.'
            ne+=' The lower-case form is the exact corpus query lemma; the abbreviation is normally capitalised.'
        evidence_ru='Достаточно ли превышения нормированной частоты, чтобы установить особое региональное значение?'
        evidence_en='Does higher normalised frequency establish a distinct regional meaning?'
        answer_ru='Нет. Оно показывает превышение частоты в выбранных подкорпусах; значение требует отдельной проверки контекстов.'
        answer_en='No. It shows enrichment in the selected subcorpora; meaning requires separate examination of contexts.'
        if lemma in special:
            evidence_ru='Почему категория '+r['pos']+' в запросе не позволяет назвать это слово существительным или прилагательным во всех употреблениях?'
            evidence_en='Why does query category '+r['pos']+' not make this word a noun or adjective in every use?'
            answer_ru='Это условие автоматического запроса. Возможны ошибки разметки и особые употребления; в учебном примере нужно определить часть речи по функции слова.'
            answer_en='It is an automatic query condition. Annotation errors and special uses are possible; identify the word class from its function in the learning example.'
        words.append({'id':f'kz-{i:03d}','lemma':lemma,'pos':r['pos'],'query_pos':r['pos'],'teaching_pos':teaching_pos,'category':category,'definition':{'ru':ru,'en':en},'example':{'ru':example,'en':'Constructed Russian learning example; interpret it using the English definition.'},'example_kind':'constructed_learning_example','note':{'ru':nr,'en':ne},'sources':sources,'frequency':nums,'provenance':{'count_source_archive':'RUN-2026-10-24-KZ-SCREEN-01.zip','archive_library_file_id':'libfile_e91b5f3314c0819199b931ab4d9869b8','kz_source':r['kz_source'],'ru_source':r['ru_source'],'original_cards':originals,'teaching_content':'editorial_prepared_2026-10-26','regional_semantics':'not_established_by_frequency','corpus_contexts_newly_collected':False},'exercises':{'recognition':{'prompt':{'ru':'Выберите объяснение слова «'+lemma+'».','en':'Choose the explanation of «'+lemma+'».'},'answer':{'ru':ru,'en':en}},'recall':{'prompt':{'ru':ru+' Введите изучаемое слово.','en':en+' Type the Russian target word.'},'answer':lemma},'evidence':{'prompt':{'ru':evidence_ru,'en':evidence_en},'answer':{'ru':answer_ru,'en':answer_en}}}})
    freeze=json.loads((STUDY/'inputs/candidate_freeze.json').read_text())
    data={'schema_version':2,'metadata':{'title':{'ru':'Русский язык в Казахстане: 94 учебные цели','en':'Russian in Kazakhstan: 94 learning targets'},'region':'Казахстан','region_id':'kz','accepted_final_word_count':94,'accepted_by_user':'2026-10-26','collection_stopped':True,'former_target':100,'collection_scope':{'corpus':'GICR','text_type':'пост','country_field':'country:ВКонтакте','target_country':'Казахстан','reference_country':'Россия','years':'all available'},'thresholds':{'minimum_target_hits':20,'minimum_target_texts':10,'minimum_ipm_ratio':2},'query_units':'exact lemma plus automatic POS; no manual semantic disambiguation','selection_claim':'frequency-screened among tested candidates, not corpus top94 and not94verified regionalisms','candidate_pool_size':24166,'candidate_pool_sha256':freeze['candidate_sha256'],'source_csv_sha256':hashlib.sha256(source_file.read_bytes()).hexdigest(),'public_data_policy':'Only this final data file is published; raw count responses and intermediate audits remain in the research archive. Source path identifiers preserve provenance but are not public download links.','teaching_content_policy':'Definitions and exercises are editorial learning material. New examples are constructed and labelled. Previously sourced cards are preserved intact in provenance.original_cards and all40originalcards in legacy_cards; those are not additional screened targets. Frequency qualification and semantic verification are distinct.','distinct_word_policy':'Exact lemma strings; alternative spellings бесбармак and бешбармак count separately; this is not morphological or etymological deduplication.','new_live_context_requests':0,'original_cards_preserved_in_matched_words':sum(len(w['provenance']['original_cards']) for w in words),'repository':'https://github.com/kopotev/regional-russian-trainer'},'words':words,'legacy_cards':[c for pack in old['packs'] for c in pack.get('cards',[])]}
    out=ROOT/'data/Kazakhstan_final.json';out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    assert len(words)==94 and len({w['lemma'] for w in words})==94
    print(json.dumps({'file':str(out),'words':len(words),'annotation_cards':sum(w['category']=='annotation' for w in words),'preserved_old_cards':data['metadata']['original_cards_preserved_in_matched_words'],'bytes':out.stat().st_size},ensure_ascii=False))

if __name__=='__main__':main()
