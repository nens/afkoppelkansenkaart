ALTER TABLE kadastraal_perceel_subdivided ADD COLUMN IF NOT EXISTS afstand_tot_bergingslocatie double precision;

with perc_berging_koppeling AS (
	SELECT DISTINCT ON (perc.id) 
			perc.id as perceel_id, 
			ST_Distance(perc.geom, berg.geom) as afstand,
			perc.maaiveldhoogte as perceel_maaiveldhoogte, 
			berg.id as bergings_id,
			berg.hoogte_median as berging_hoogte,
			(perc.maaiveldhoogte - berg.hoogte_median)/(ST_Distance(perc.geom, berg.geom) + 0.01) as verhang
	FROM 	kadastraal_perceel_subdivided AS perc
	LEFT JOIN potentiele_bergingslocaties AS berg 
		ON 	ST_DWithin(perc.geom, berg.geom, 100) AND 
			(perc.maaiveldhoogte - berg.hoogte_median) / (ST_Distance(perc.geom, berg.geom) + 0.01) > (1/100.0)
	ORDER BY perc.uid,
			ST_Distance(perc.geom, berg.geom)
	)
UPDATE 	kadastraal_perceel_subdivided AS tgt
SET 	afstand_tot_bergingslocatie = src.afstand 
FROM 	perc_berging_koppeling AS src
WHERE 	src.perceel_id = tgt.id
; 
