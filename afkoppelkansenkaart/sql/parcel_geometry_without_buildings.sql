ALTER TABLE kadastraal_perceel_subdivided ADD COLUMN IF NOT EXISTS geom_geenpand geometry(MultiPolygonZ, 28992);

UPDATE kadastraal_perceel_subdivided set geom_geenpand = NULL;

WITH perc_zonder_pand AS (
	SELECT 	perc.id, 
			(ST_Dump(ST_Difference(perc.geom, ST_Union(pand.geom)))).geom AS geom
	FROM	bgt_inlooptabel AS pand
	JOIN 	kadastraal_perceel_subdivided AS perc
	ON 		ST_Intersects(pand.geom, perc.geom)
	WHERE 	pand.type_verharding = 'dak'
	GROUP BY perc.id, perc.geom
),
filtered AS (
	SELECT 	id, 
			ST_Multi(ST_Collect(geom)) AS geom 
	FROM 	perc_zonder_pand 
	WHERE 	ST_GeometryType(geom) = 'ST_Polygon'
	GROUP BY id
)
UPDATE	kadastraal_perceel_subdivided AS pt
SET 	geom_geenpand = pzp.geom
FROM 	filtered AS pzp
WHERE 	pt.id = pzp.id
;

UPDATE 	kadastraal_perceel_subdivided 
SET 	geom_geenpand = ST_Multi(geom)
WHERE 	geom_geenpand IS NULL

ALTER TABLE kadastraal_perceel_subdivided ADD COLUMN IF NOT EXISTS area_geom_geenpand double precision; 
SET 	area_geom_geenpand = ST_Area((geom_geenpand)
;

