ALTER TABLE kadastraal_perceel_subdivided ADD COLUMN IF NOT EXISTS afstand_tot_rwzi double precision;

with perceel_rwzi_koppeling AS (
	SELECT DISTINCT ON (perc.id) 
			perc.id as perceel_id, 
			ST_Distance(perc.geom, rwzi.geom) as afstand
	FROM 	kadastraal_perceel_subdivided AS perc,
			rwzi AS berg 
	ORDER BY perc.id,
			ST_Distance(perc.geom, rwzi.geom)
	)
UPDATE 	kadastraal_perceel_subdivided AS tgt
SET 	afstand_tot_rwzi = src.afstand 
FROM 	perceel_rwzi_koppeling AS src
WHERE 	src.perceel_id = tgt.id
; 
