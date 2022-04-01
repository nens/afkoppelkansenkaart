DROP TABLE IF EXISTS potentiele_bergingslocaties;
CREATE TABLE potentiele_bergingslocaties AS 
SELECT 	'BGT vlak '|| bgt_identificatie AS beschrijving,
		type_verharding, 
		geom 
FROM 	bgt_inlooptabel
WHERE 	type_verharding = 'water'
		OR (type_verharding = 'onverhard' AND ST_Area(geom) = 30)
;

ALTER TABLE potentiele_bergingslocaties ADD COLUMN id serial;
ALTER TABLE potentiele_bergingslocaties ADD PRIMARY KEY (id);
CREATE INDEX ON potentiele_bergingslocaties USING gist(geom);