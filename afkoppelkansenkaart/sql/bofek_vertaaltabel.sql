--- OMZETTEN BOFEK BODEMTYPES NAAR K-WAARDEN ( http://www.grondwaterformules.nl/index.php/vuistregels/ondergrond/doorlatendheid-per-grondsoort )
DROP TABLE IF EXISTS bofek_vertaaltabel;
CREATE TABLE bofek_vertaaltabel (id serial primary key, pawn_code integer, beschrijving text, doorlatendheid double precision);
INSERT INTO bofek_vertaaltabel (pawn_code, beschrijving, doorlatendheid) VALUES
	(1, 'Veengrond met veraarde bovengrond', 0.05),
	(2, 'Veengrond met veraarde bovengrond, zand', 0.05),
	(3, 'Veengrond met kleidek', 0.005),
	(4, 'Veengrond met kleidek op zand', 0.005),
	(5, 'Veengrond met zanddek op zand', 0.45),
	(6, 'Veengrond op ongerijpte klei', 0.005),
	(7, 'Stuifzand', 10),
	(8, 'Podzol (leemarm, fijn zand)', 5),
	(9, 'Podzol (zwak lemig, fijn zand)', 2),
	(10, 'Podzol (zwak lemig, fijn zand op grof zand)', 2),
	(11, 'Podzol (lemig keileem)', 0.5),
	(12, 'Enkeerd (zwak lemig, fijn zand)', 2),
	(13, 'Beekeerd (lemig fijn zand)', 0.45),
	(14, 'Podzol (grof zand)', 10),
	(15, 'Zavel', 0.5),
	(16, 'Lichte klei', 0.05),
	(17, 'Zware klei', 0.0001),
	(18, 'Klei op veen'0.01),
	(19, 'Klei op zand', 0.01),
	(20, 'Klei op grof zand', 0.01),
	(21, 'Leem', 0.05)
;
