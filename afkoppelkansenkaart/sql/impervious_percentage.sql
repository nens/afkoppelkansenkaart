-- Attribuut verhard_oppervlak moet worden gevuld met [onbebouwd oppervlak] * (1-[groenpercentage])
-- Attribuut verhard_percentage moet worden gevuld met [verhard oppervlak] / [perceeloppervlak]
ALTER TABLE kadastraal_perceel_subdivided ADD COLUMN IF NOT EXISTS verhard_oppervlak double precision;
ALTER TABLE kadastraal_perceel_subdivided ADD COLUMN IF NOT EXISTS verhard_percentage double precision;

UPDATE 	kadastraal_perceel_subdivided SET verhard_oppervlak = ST_Area(geom_geenpand) * (1-{groenpercentage});
UPDATE 	kadastraal_perceel_subdivided SET verhard_percentage = verhard_oppervlak / oppervlakte_perceel;
		