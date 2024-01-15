lNames = ['Deutschland',
'Albert_Einstein',
'Carl_Friedrich_Gauß',
'Wilhelm_Röntgen',
'Marie_Curie',
'Alexander_von_Humboldt',
'Johannes_Kepler',
'Konrad_Zuse',
'Otto_Hahn',
'Werner_Heisenberg',
'Italien',
'Leonardo_da_Vinci',
'Galileo_Galilei',
'Nicolaus_Copernicus',
'Marco_Polo',
'England',
'Isaac_Newton',
'Charles_Darwin',
'Stephen_Hawking',
'Alan_Turing',
'Frankreich',
'Louis_Pasteur',
'Marie_Curie',
'Antoine_de_Saint-Exupéry',
'Spanien',
'Christoph_Kolumbus',
'Ferdinand_Magellan',
'Portugal',
'Vasco_da_Gama',
'Vereinigte_Staaten',
'Thomas_Edison',
'Alexander_Graham_Bell',
'Albert_Einstein',
'Neil_Armstrong',
'Nach_Fachgebieten',
'',
'Astronomie',
'Galileo_Galilei',
'Nicolaus_Copernicus',
'Johannes_Kepler',
'Edwin_Hubble',
'Stephen_Hawking',
'Mathematik',
'Carl_Friedrich_Gauß',
'Isaac_Newton',
'Gottfried_Wilhelm_Leibniz',
'Srinivasa_Ramanujan',
'Alan_Turing',
'Physik',
'Albert_Einstein',
'Marie_Curie',
'Niels_Bohr',
'Stephen_Hawking',
'Max_Planck',
'Chemie',
'Marie_Curie',
'Dmitri_Mendelejew',
'Fritz_Haber',
'Linus_Pauling',
'Robert_Oppenheimer',
'Biologie',
'Charles_Darwin',
'Gregor_Mendel',
'Louis_Pasteur',
'Alexander_Fleming',
'James_Watson',
'Medizin',
'Alexander_Fleming',
'Louis_Pasteur',
'Jonas_Salk',
'Albert_Sabin',
'Marie_Curie',
'Technik',
'Thomas_Edison',
'Alexander_Graham_Bell',
'Henry_Ford',
'Nikola_Tesla',
'Wernher_von_Braun',
'Kunst',
'Leonardo_da_Vinci',
'Michelangelo',
'Vincent_van_Gogh',
'Pablo_Picasso',
'Andy_Warhol']

lNames_new = []
for name in lNames:
  print(name)
  lParts = name.split('_')[1:]
  if lParts:
    if len(lParts) > 1:
      lNames_new.append('_'.join(lParts))
    else:
      lNames_new.append(lParts[0])
  else:
    lNames_new.append(name)

print()
print(lNames_new)

lNames_new = [
  'Einstein',
  'Gauß',
  'Röntgen',
  'Curie',
  'von_Humboldt',
  'Kepler',
  'Zuse',
  'Hahn',
  'Heisenberg',
  'da_Vinci',
  'Galilei',
  'Copernicus',
  'Polo',
  'Newton',
  'Darwin',
  'Hawking',
  'Turing',
  'Pasteur',
  'Curie',
  'de_Saint-Exupéry',
  'Kolumbus',
  'Magellan',
  'da_Gama',
  'Edison',
  'Bell',
  'Einstein',
  'Armstrong',
  'Galilei',
  'Copernicus',
  'Kepler',
  'Hubble',
  'Hawking',
  'Gauß',
  'Newton',
  'Leibniz',
  'Ramanujan',
  'Turing',
  'Einstein',
  'Curie',
  'Bohr',
  'Hawking',
  'Planck',
  'Curie',
  'Mendelejew',
  'Haber',
  'Pauling',
  'Oppenheimer',
  'Darwin',
  'Mendel',
  'Pasteur',
  'Fleming',
  'Watson',
  'Fleming',
  'Pasteur',
  'Salk', 
  'Sabin',
  'Curie',
  'Edison',
  'Bell',
  'Ford',
  'Tesla',
  'von_Braun',
  'da_Vinci',
  'Michelangelo',
  'van_Gogh',
  'Picasso',
  'Warhol'
]