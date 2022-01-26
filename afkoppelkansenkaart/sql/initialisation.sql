DELETE FROM score_zoektabel;
DELETE FROM weging;
DELETE FROM criterium;
DELETE FROM domein;
DELETE FROM hoofdonderdeel;

INSERT INTO hoofdonderdeel (id, naam, omschrijving)
VALUES  (1, 'fysieke_kansrijkheid', 'Fysieke kansrijkheid'),
        (2, 'effectiviteit', 'Effectiviteit')
;

INSERT INTO domein (id, naam, omschrijving, hoofdonderdeel_id)
values  (1, 'verharding', 'Verharding', 1),
        (2, 'infiltratie', 'Infiltratie', 1),
        (3, 'afstand', 'Afstand', 1),
        (4, 'transport', 'Transport', 2),
        (5, 'oppervlaktewater', 'Oppervlaktewater', 2),
        (6, 'wateroverlast', 'Wateroverlast', 2),
        (7, 'efficientie', 'Effici�ntie', 2)
;

INSERT INTO criterium (id, naam, omschrijving, domein_id)
VALUES  (1, 'verhardingspercentage', 'Percentage verharding', 1),
        (2, 'bebouwingspercentage', 'Percentage bebouwing', 1),
        (3, 'bodemberging', 'Hoeveelheid berging ondergrond (diepte GHG beneden maaiveld)', 2),
        (4, 'doorlatendheid', 'Doorlatendheid (k-waarde)', 2),
        (5, 'afstand_tot_bergingslocatie', 'Afstand tot eventuele bergingslocatie', 3),
        (6, 'stelseltype', 'Type stelsel dichtsbijzijnde riolering', 4),
        (7, 'aantal_verpompen', 'Aantal keer verpompen naar RWZI', 4),
        (8, 'afstand_rwzi', 'Transportafstand naar RWZI', 4),
        (9, 'belasting_oppervlaktewater', 'Belasting oppervlaktewater waarin riolering overstort', 5),
        (10, 'gebiedstype_wateroverlast', 'Soort gebied potentie verminderen kans op wateroverlast benedenstrooms', 6),
        (11, 'af_te_koppelen_oppervlak', 'Grootte van het af te koppelen verhard oppervlak', 7)
;

INSERT INTO weging (score_type, score_id, factor)
VALUES  ('criterium', 1, 1),
        ('criterium', 2, 1),
        ('criterium', 3, 1),
        ('criterium', 4, 1),
        ('criterium', 5, 1),
        ('criterium', 6, 1),
        ('criterium', 7, 1),
        ('criterium', 8, 1),
        ('criterium', 9, 1),
        ('criterium', 10, 1),
        ('criterium', 11, 1),
        ('domein', 1, 1),
        ('domein', 2, 1),
        ('domein', 3, 1),
        ('domein', 4, 1),
        ('domein', 5, 1),
        ('domein', 6, 1),
        ('domein', 7, 1),
        ('hoofdonderdeel', 1, 1),
        ('hoofdonderdeel', 2, 1)
;

INSERT INTO score_zoektabel (criterium_id, omschrijving, code, klasse_ondergrens, klasse_bovengrens, score)
VALUES  (1,'Nagenoeg volledig onverhard',   1,0,25,3),
        (1,'Grotendeels onverhard',         2,25,50,2),
        (1,'Grotendeels verhard',           3,50,75,1),
        (1,'Nagenoeg volledig verhard',     4,75,100,0),

        (2,'Nagenoeg volledig onbebouwd',   1,0,25,3),
        (2,'Grotendeels onbebouwd',         2,25,50,2),
        (2,'Grotendeels bebouwd',           3,50,75,1),
        (2,'Nagenoeg volledig bebouwd',     4,75,100,0),

        (3,'Weinig tot geen',               1,-9999,0.7,0),
        (3,'Matig',                         2,0.7,1.5,2),
        (3,'Veel',                          3,1.5,9999,3),

        (4,'Slecht',                        1,0,0.1,0),
        (4,'Matig',                         2,0.1,0.5,1),
        (4,'Goed',                          3,0.5,1,2),
        (4,'Zeer goed',                     4,1,9999,3),

        (5,'Naastgelegen',                  1,0,10.0,3),
        (5,'Enige afstand',                 2,10.0,50.0,2),
        (5,'Ver weg',                       3,50.0,100,1),
        (5,'Geen lagergelegen bergingslocatie',4,100,9999,0),

        (7,'Geen riolering binnen 100 m',   1,-9999,-1,0),
        (7,'Vrijverval',                    2,-1,0.0,1),
        (7,'1x pompen',                     3,0.0,1.0,2),
        (7,'2x of vaker pompen',            4,1.0,9999,3),

        (8,'Perceel niet aangesloten op riolering',1,-9999,0,0),
        (8,'Korte afstand',                 2,0,2000.0,1),
        (8,'Middelmatige afstand',          3,2000.0,4000.0,2),
        (8,'Verre afstand',                 4,4000.0,999999,3),

        (11,'Klein',                        1,0,10.0,0),
        (11,'Middelmatig',                  2,10.0,100.0,1),
        (11,'Groot',                        3,100.0,1000,2),
        (11,'Heel groot',                   4,1000,999999,3)
;

INSERT INTO score_zoektabel (criterium_id, omschrijving, code, score)
VALUES  (6,'Gemengd',                       1,3),
        (6,'Verbeterd gemengd',             2,2),
        (6,'RWA verbeterd gescheiden',      3,1),
        (6,'RWA gescheiden',                4,1),
        (6,'RWA naar bodem of infiltratievoorziening',5,0),
        (6,'Afwatering op maaiveld',        6,0),

        (9,'T=1/6',                         1,1),
        (9,'T=2',                           2,2),
        (9,'T=5',                           3,3),
        (9,'onbekend',                      4,2),
        (9,'nvt',                           5,0),

        (10,'Knelpunt',                     1,2),
        (10,'Invloedsgebied',               2,3),
        (10,'Neutraal',                     3,0)
;

