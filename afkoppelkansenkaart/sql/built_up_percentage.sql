ALTER TABLE kadastraal_perceel_subdivided ADD COLUMN IF NOT EXISTS oppervlakte_bebouwing double precision; 
ALTER TABLE kadastraal_perceel_subdivided ADD COLUMN IF NOT EXISTS percentage_bebouwing  double precision; 

WITH daken_merged as (
	SELECT 	perc.id as perceel_id, 
			ST_Buffer(ST_Collect(pand.geom), 0) AS geom
	FROM	kadastraal_perceel_subdivided AS perc
	JOIN 	bgt_inlooptabel AS pand
	ON 		ST_Intersects(pand.geom, perc.geom) 
	        AND pand.type_verharding = 'dak'
	GROUP BY perceel_id
),
intersection AS (
	SELECT 	perc.id, 
			ST_Area(ST_Intersection(perc.geom, pand.geom)) AS oppervlakte_bebouwing
	FROM	kadastraal_perceel_subdivided AS perc
	LEFT JOIN 	daken_merged AS pand
	ON 		pand.perceel_id = perc.id
)
UPDATE 	kadastraal_perceel_subdivided AS tgt
SET 	oppervlakte_bebouwing = COALESCE(src.oppervlakte_bebouwing, 0),
		percentage_bebouwing = COALESCE(src.oppervlakte_bebouwing / ST_Area(tgt.geom) * 100, 0)
FROM 	intersection AS src
WHERE 	src.id = tgt.id
;
