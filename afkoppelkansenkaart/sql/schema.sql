DROP TABLE IF EXISTS perceel;
DROP TABLE IF EXISTS buurt;
DROP TABLE IF EXISTS wijk;
DROP TABLE IF EXISTS score_zoektabel;
DROP TABLE IF EXISTS hoofdonderdeel;
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
	omschrijving text,
	code integer,
	klasse_ondergrens real,
	klasse_bovengrens real,
	score integer,
	UNIQUE(criterium_id, code)
)
;

CREATE TABLE hoofdonderdeel (
	id integer PRIMARY KEY AUTOINCREMENT,
	naam text,
	omschrijving text
);

CREATE TABLE domein (
	id integer PRIMARY KEY AUTOINCREMENT,
	naam text,
	omschrijving text,
	hoofdonderdeel_id integer REFERENCES hoofdonderdeel(id)
);

CREATE TABLE criterium (
	id integer PRIMARY KEY AUTOINCREMENT,
	naam text,
	omschrijving text,
	domein_id integer REFERENCES domein(id)
);

CREATE TABLE weging (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	score_type TEXT CHECK( score_type IN ('criterium', 'domein', 'hoofdonderdeel') ) NOT NULL,
	score_id integer,
	factor real
);

CREATE TABLE perceel_criteriumwaarde (
    id integer primary key autoincrement,
    perceel_id integer references perceel (id),
    criterium_id integer references criterium (id),
    waarde real
);

----
CREATE VIEW IF NOT EXISTS perceel_criteriumscore AS
SELECT  waarde.id,
        waarde.perceel_id,
        waarde.criterium_id,
        coalesce (klasse.score, categorie.score) AS score
FROM    perceel_criteriumwaarde AS waarde
LEFT JOIN score_zoektabel AS klasse
    ON  waarde.criterium_id = klasse.criterium_id
        AND waarde.waarde > klasse.klasse_ondergrens
        AND waarde.waarde <= klasse.klasse_bovengrens
LEFT JOIN score_zoektabel AS categorie
    ON  waarde.criterium_id = categorie.criterium_id
        AND waarde.waarde = categorie.code
;

CREATE VIEW IF NOT EXISTS perceel_domeinscore AS
SELECT  pcs.id,
        pcs.perceel_id,
        domein.id AS domein_id,
        sum(pcs.score * weging.factor) / sum(weging.factor) AS score
FROM    perceel_criteriumscore AS pcs
LEFT JOIN criterium
    ON  pcs.criterium_id = criterium.id
LEFT JOIN domein
    ON  criterium.domein_id = domein.id
LEFT JOIN weging 
    ON  score_type = 'criterium'
        AND score_id = criterium.id
GROUP BY pcs.id, pcs.perceel_id, domein.id
;

CREATE VIEW IF NOT EXISTS perceel_hoofdonderdeelscore AS
SELECT  pds.id,
        pds.perceel_id,
        hoofdonderdeel.id AS hoofdonderdeel_id,
        sum(pds.score * weging.factor) / sum(weging.factor) AS score
FROM    perceel_domeinscore AS pds
LEFT JOIN domein
    ON  pds.domein_id = domein.id
LEFT JOIN hoofdonderdeel
    ON  domein.hoofdonderdeel_id = hoofdonderdeel.id
LEFT JOIN weging 
    ON  score_type = 'domein'
        AND score_id = domein.id
GROUP BY pds.id, pds.perceel_id, domein.id
;

CREATE VIEW IF NOT EXISTS perceel_eindscore AS
SELECT  phs.id,
        phs.perceel_id,
        sum(phs.score * weging.factor) / sum(weging.factor) AS score
FROM    perceel_hoofdonderdeelscore AS phs
LEFT JOIN hoofdonderdeel
    ON  phs.hoofdonderdeel_id = hoofdonderdeel.id
LEFT JOIN weging
    ON  score_type = 'hoofdonderdeel'
        AND score_id = hoofdonderdeel.id
GROUP BY phs.id, phs.perceel_id
;

CREATE VIEW IF NOT EXISTS buurt_eindscore AS
SELECT  buurt.*,
        ROUND(SUM(ST_Area(perceel) * eind.score) / SUM(ST_Area(perceel)), 3) as gemiddelde_eindscore
FROM    buurt
LEFT JOIN perceel
    ON  ST_Intersects(perceel.geom, buurt.geom)
JOIN    perceel_eindscore AS eind
    ON  perceel.id = eind.id
GROUP BY buurt.naam
;


CREATE VIEW IF NOT EXISTS wijk_eindscore AS
SELECT  wijk.*,
        ROUND(SUM(ST_Area(perceel) * eind.score) / SUM(ST_Area(perceel)), 3) as gemiddelde_eindscore
FROM    wijk
LEFT JOIN perceel
    ON  ST_Intersects(perceel.geom, wijk.geom)
JOIN    perceel_eindscore AS eind
    ON  perceel.id = eind.id
GROUP BY wijk.naam
;


--CREATE VIEW IF NOT EXISTS perceel_criteriumscores AS
--SELECT	perceel.*,
--        zoek_1.score as score_verhard_percentage,
--        zoek_2.score as score_percentage_bebouwing,
--        zoek_3.score as score_ghg_tov_maaiveld,
--        zoek_4.score as score_doorlatendheid_bodem,
--        zoek_5.score as score_afstand_tot_bergingslocatie,
--        zoek_6.score as score_type_rioolstelsel,
--        zoek_7.score as score_aantal_keer_verpompen,
--        zoek_8.score as score_afstand_tot_rwzi,
--        zoek_9.score as score_kwetsbaarheid_oppervlaktewater,
--        zoek_10.score as score_type_gebied,
--        zoek_11.score as score_verhard_oppervlak
--FROM    perceel
--
---- criterium 1: verhard_percentage (klasse)
--LEFT JOIN    score_zoektabel AS zoek_1
--    ON  perceel.verhard_percentage > zoek_1.klasse_ondergrens
--        AND perceel.verhard_percentage <= zoek_1.klasse_bovengrens
--        AND zoek_1.criterium_id = 1
--
---- criterium 2: percentage_bebouwing (klasse)
--LEFT JOIN    score_zoektabel AS zoek_2
--    ON  perceel.percentage_bebouwing > zoek_2.klasse_ondergrens
--        AND perceel.percentage_bebouwing <= zoek_2.klasse_bovengrens
--        AND zoek_2.criterium_id = 2
--
---- criterium 3: ghg_tov_maaiveld (klasse)
--LEFT JOIN    score_zoektabel AS zoek_3
--    ON  perceel.ghg_tov_maaiveld > zoek_3.klasse_ondergrens
--        AND perceel.ghg_tov_maaiveld <= zoek_3.klasse_bovengrens
--        AND zoek_3.criterium_id = 3
--
--
---- criterium 4: doorlatendheid_bodem (klasse)
--LEFT JOIN    score_zoektabel AS zoek_4
--    ON  perceel.ghg_tov_maaiveld > zoek_4.klasse_ondergrens
--        AND perceel.ghg_tov_maaiveld <= zoek_4.klasse_bovengrens
--        AND zoek_4.criterium_id = 4
--
---- criterium 5: afstand_tot_bergingslocatie (klasse)
--LEFT JOIN    score_zoektabel AS zoek_5
--    ON  perceel.afstand_tot_bergingslocatie > zoek_5.klasse_ondergrens
--        AND perceel.afstand_tot_bergingslocatie <= zoek_5.klasse_bovengrens
--        AND zoek_5.criterium_id = 5
--
---- criterium 6: type_rioolstelsel (categorie)
--LEFT JOIN    score_zoektabel AS zoek_6
--    ON  perceel.type_rioolstelsel = zoek_6.categorie
--        AND zoek_6.criterium_id = 6
--
---- criterium 7: aantal_keer_verpompen (klasse)
--LEFT JOIN    score_zoektabel AS zoek_7
--    ON  perceel.aantal_keer_verpompen > zoek_7.klasse_ondergrens
--        AND perceel.aantal_keer_verpompen <= zoek_7.klasse_bovengrens
--        AND zoek_7.criterium_id = 7
--
---- criterium 8: afstand_tot_rwzi (klasse)
--LEFT JOIN    score_zoektabel AS zoek_8
--    ON  perceel.afstand_tot_rwzi > zoek_8.klasse_ondergrens
--        AND perceel.afstand_tot_rwzi <= zoek_8.klasse_bovengrens
--        AND zoek_8.criterium_id = 8
--
---- criterium 9: kwetsbaarheid_oppervlaktewater (categorie)
--LEFT JOIN    score_zoektabel AS zoek_9
--    ON  perceel.kwetsbaarheid_oppervlaktewater = zoek_9.categorie
--        AND zoek_9.criterium_id = 9
--
---- criterium 10: type_gebied (categorie)
--LEFT JOIN    score_zoektabel AS zoek_10
--    ON  perceel.type_gebied = zoek_10.categorie
--        AND zoek_10.criterium_id = 10
--
---- criterium 11: verhard_oppervlak (klasse)
--LEFT JOIN    score_zoektabel AS zoek_11
--    ON  perceel.verhard_oppervlak > zoek_11.klasse_ondergrens
--        AND perceel.verhard_oppervlak <= zoek_11.klasse_bovengrens
--        AND zoek_11.criterium_id = 11
--;

