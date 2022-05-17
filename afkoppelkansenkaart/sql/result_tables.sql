DROP TABLE IF EXISTS resultaat_afkoppelrendementskaart;
DROP TABLE IF EXISTS resultaat_buurt_eindscore;
DROP TABLE IF EXISTS resultaat_wijk_eindscore;
CREATE TABLE resultaat_afkoppelrendementskaart AS SELECT * FROM afkoppelkansenkaart;
CREATE TABLE resultaat_buurt_eindscore AS SELECT * FROM buurt_eindscore;
CREATE TABLE resultaat_wijk_eindscore AS SELECT * FROM wijk_eindscore;