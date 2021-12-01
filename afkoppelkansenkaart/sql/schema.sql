DROP TABLE IF EXISTS perceel;
DROP TABLE IF EXISTS buurt;
DROP TABLE IF EXISTS wijk;
DROP TABLE IF EXISTS score_zoektabel;
DROP TABLE IF EXISTS eindscore_deel;
DROP TABLE IF EXISTS domein;
DROP TABLE IF EXISTS criterium;
DROP TABLE IF EXISTS weging;

DROP VIEW IF EXISTS perceel_criteriumscores;

CREATE TABLE perceel (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	brk_lokaalid TEXT, 
	brk_perceelnummer TEXT, 
	oppervlakte_perceel REAL, 
	gemeentelijk_eigendom text, 
	oppervlakte_bebouwing REAL, 
	percentage_bebouwing REAL, 
	verhard_oppervlak REAL, 
	verhard_percentage REAL, 
	maaiveldhoogte REAL, 
	bodemsoort TEXT, 
	doorlatendheid_bodem REAL, 
	ghg_tov_maaiveld REAL, 
	afstand_tot_bergingslocatie REAL, 
	code_dichtsbijzijnde_rioolleiding TEXT, 
	type_rioolstelsel TEXT, 
	kwetsbaarheid_oppervlaktewater TEXT, 
	aantal_keer_verpompen INTEGER, 
	afstand_tot_rwzi TEXT, 
	type_gebied TEXT,
	geom MULTIPOLYGON
)
;

CREATE TABLE buurt (
	id integer primary key autoincrement,
	code text,
	naam text,
	aantal_inwoners integer,
	geom MULTIPOLYGON
)
;

CREATE TABLE wijk (
	id integer primary key autoincrement,
	code text,
	naam text,
	aantal_inwoners integer,
	geom MULTIPOLYGON
)
;

CREATE TABLE score_zoektabel (
	id integer PRIMARY KEY AUTOINCREMENT,
	criterium_id integer,
	categorie text,
	klasse_ondergrens real,
	klasse_bovengrens real,
	score integer
)
;

CREATE TABLE eindscore_deel (
	id integer PRIMARY KEY AUTOINCREMENT,
	omschrijving text
);

CREATE TABLE domein (
	id integer PRIMARY KEY AUTOINCREMENT,
	omschrijving text,
	eindscore_deel_id integer REFERENCES eindscore_deel(id)
);

CREATE TABLE criterium (
	id integer PRIMARY KEY AUTOINCREMENT,
	omschrijving text,
	domein_id integer REFERENCES domein(id)
);

CREATE TABLE weging (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	score_type TEXT CHECK( score_type IN ('criterium', 'domein', 'eindscore_deel') ) NOT NULL,
	score_id integer,
	factor real
);

----
CREATE VIEW IF NOT EXISTS perceel_criteriumscores AS 
SELECT	perceel.*,
        zoek_1.score as score_verhard_percentage,
        zoek_2.score as score_percentage_bebouwing,
        zoek_3.score as score_ghg_tov_maaiveld,
        zoek_4.score as score_doorlatendheid_bodem,
        zoek_5.score as score_afstand_tot_bergingslocatie,
        zoek_6.score as score_type_rioolstelsel,
        zoek_7.score as score_aantal_keer_verpompen,
        zoek_8.score as score_afstand_tot_rwzi,
        zoek_9.score as score_kwetsbaarheid_oppervlaktewater,
        zoek_10.score as score_type_gebied,
        zoek_11.score as score_verhard_oppervlak        
FROM    perceel

-- criterium 1: verhard_percentage (klasse)
LEFT JOIN    score_zoektabel AS zoek_1
    ON  perceel.verhard_percentage > zoek_1.klasse_ondergrens
        AND perceel.verhard_percentage <= zoek_1.klasse_bovengrens
        AND zoek_1.criterium_id = 1

-- criterium 2: percentage_bebouwing (klasse)
LEFT JOIN    score_zoektabel AS zoek_2
    ON  perceel.percentage_bebouwing > zoek_2.klasse_ondergrens
        AND perceel.percentage_bebouwing <= zoek_2.klasse_bovengrens
        AND zoek_2.criterium_id = 2

-- criterium 3: ghg_tov_maaiveld (klasse)
LEFT JOIN    score_zoektabel AS zoek_3
    ON  perceel.ghg_tov_maaiveld > zoek_3.klasse_ondergrens
        AND perceel.ghg_tov_maaiveld <= zoek_3.klasse_bovengrens
        AND zoek_3.criterium_id = 3
        

-- criterium 4: doorlatendheid_bodem (klasse)
LEFT JOIN    score_zoektabel AS zoek_4
    ON  perceel.ghg_tov_maaiveld > zoek_4.klasse_ondergrens
        AND perceel.ghg_tov_maaiveld <= zoek_4.klasse_bovengrens
        AND zoek_4.criterium_id = 4
        
-- criterium 5: afstand_tot_bergingslocatie (klasse)
LEFT JOIN    score_zoektabel AS zoek_5
    ON  perceel.afstand_tot_bergingslocatie > zoek_5.klasse_ondergrens
        AND perceel.afstand_tot_bergingslocatie <= zoek_5.klasse_bovengrens
        AND zoek_5.criterium_id = 5
        
-- criterium 6: type_rioolstelsel (categorie)
LEFT JOIN    score_zoektabel AS zoek_6
    ON  perceel.type_rioolstelsel = zoek_6.categorie
        AND zoek_6.criterium_id = 6

-- criterium 7: aantal_keer_verpompen (klasse)
LEFT JOIN    score_zoektabel AS zoek_7
    ON  perceel.aantal_keer_verpompen > zoek_7.klasse_ondergrens
        AND perceel.aantal_keer_verpompen <= zoek_7.klasse_bovengrens
        AND zoek_7.criterium_id = 7

-- criterium 8: afstand_tot_rwzi (klasse)
LEFT JOIN    score_zoektabel AS zoek_8
    ON  perceel.afstand_tot_rwzi > zoek_8.klasse_ondergrens
        AND perceel.afstand_tot_rwzi <= zoek_8.klasse_bovengrens
        AND zoek_8.criterium_id = 8
        
-- criterium 9: kwetsbaarheid_oppervlaktewater (categorie)
LEFT JOIN    score_zoektabel AS zoek_9
    ON  perceel.kwetsbaarheid_oppervlaktewater = zoek_9.categorie
        AND zoek_9.criterium_id = 9

-- criterium 10: type_gebied (categorie)
LEFT JOIN    score_zoektabel AS zoek_10
    ON  perceel.type_gebied = zoek_10.categorie
        AND zoek_10.criterium_id = 10

-- criterium 11: verhard_oppervlak (klasse)
LEFT JOIN    score_zoektabel AS zoek_11
    ON  perceel.verhard_oppervlak > zoek_11.klasse_ondergrens
        AND perceel.verhard_oppervlak <= zoek_11.klasse_bovengrens
        AND zoek_11.criterium_id = 11
;    
        
--- TODO

-- Toevoegen buurt, wijk


-- Toevoegen aggregatie op buurt, wijk


