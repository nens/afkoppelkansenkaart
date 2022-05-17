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
	gebiedstype_wateroverlast TEXT,
	geom MULTIPOLYGON
)
;

CREATE TABLE buurt (
	id integer primary key autoincrement,
	code text,
	naam text UNIQUE NOT NULL,
	aantal_inwoners integer,
	geom MULTIPOLYGON
)
;

CREATE TABLE wijk (
	id integer primary key autoincrement,
	code text,
	naam text UNIQUE NOT NULL,
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
