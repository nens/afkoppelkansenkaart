ALTER TABLE kadastraal_perceel_subdivided ADD COLUMN IF NOT EXISTS oppervlakte_bebouwing double precision; 
ALTER TABLE kadastraal_perceel_subdivided ADD COLUMN IF NOT EXISTS percentage_bebouwing  double precision; 

WITH intersection AS (
	SELECT 	perc.id, 
			COALESCE(ST_Area(ST_Intersection(perc.geom, pand.geom)), 0) AS oppervlakte_bebouwing
	FROM	bgt_inlooptabel AS pand
	LEFT JOIN 	kadastraal_perceel_subdivided AS perc
	ON 		ST_Intersects(pand.geom, perc.geom)
	WHERE 	pand.type_verharding = 'dak'
)
UPDATE 	kadastraal_perceel_subdivided AS tgt
SET 	oppervlakte_bebouwing = src.oppervlakte_bebouwing,
		percentage_bebouwing = src.oppervlakte_bebouwing / ST_Area(tgt.geom)
FROM 	intersection AS src
;
