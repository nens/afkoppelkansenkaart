-- Match perceel met bgt vlak waarmee de intersectie het grootste is
DROP TABLE IF EXISTS bgt_vlakken_merged;
CREATE TABLE bgt_vlakken_merged AS
SELECT 	perc.id AS perceel_id,
		bgt.gemengd_riool, 
		bgt.hemelwaterriool,
		bgt.vgs_hemelwaterriool,
--     	bgt.vuilwaterriool,
		bgt.infiltratievoorziening,
		bgt.open_water,
		bgt.maaiveld,
		ST_Buffer(ST_Union(bgt.geom),0) AS geom
FROM 	kadastraal_perceel_subdivided AS perc
JOIN 	bgt_inlooptabel AS bgt
	ON	ST_Intersects(perc.geom, bgt.geom)
GROUP BY perc.id, 		
		bgt.gemengd_riool, 
		bgt.hemelwaterriool,
		bgt.vgs_hemelwaterriool,
--     	bgt.vuilwaterriool,
		bgt.infiltratievoorziening,
		bgt.open_water,
		bgt.maaiveld
;

CREATE INDEX ON bgt_vlakken_merged USING gist(geom);

-- UPDATE bgt_inlooptabel SET geom = ST_Buffer(geom, 0);
-- UPDATE kadastraal_perceel_subdivided SET geom = ST_Force3D(ST_Multi(ST_Buffer(geom,0)))::geometry(MultiPolygonZ, 28992);

WITH type_rioolstelsel_per_perceel AS (
	SELECT 	DISTINCT ON (perc.id)
			perc.id,
			CASE 
				WHEN bgt.gemengd_riool = 100 THEN 1 -- Gemengd
				WHEN bgt.hemelwaterriool = 100 THEN 4 -- Gescheiden RWA/DWA
				WHEN bgt.vgs_hemelwaterriool = 100 THEN 3 -- Verbeterd gescheiden RWA/DWA
	--     		WHEN bgt.vuilwaterriool = 100, THEN ja gekkigheid zeg dit doen we niet hoor
				WHEN bgt.infiltratievoorziening = 100 THEN 5 -- Infiltratievoorziening (RWA-IT/DWA)
				WHEN bgt.open_water = 100 THEN 7 -- Open water 
				WHEN bgt.maaiveld = 100 THEN 6 -- Maaiveld
				WHEN bgt.gemengd_riool < 100 AND bgt.gemengd_riool > 0 AND bgt.hemelwaterriool > 0 THEN 8 -- 'Gescheiden RWA/Gemengd'
			END AS type_rioolstelsel
	FROM 	kadastraal_perceel_subdivided AS perc
	JOIN	bgt_vlakken_merged AS bgt
		ON	perc.id = bgt.perceel_id
	ORDER BY 
			id, 
			ST_Area(ST_Intersection(bgt.geom, perc.geom)) DESC
)
UPDATE 	kadastraal_perceel_subdivided AS tgt
SET 	type_rioolstelsel = src.type_rioolstelsel
FROM 	type_rioolstelsel_per_perceel AS src
WHERE 	tgt.id = src.id
;

DROP TABLE IF EXISTS bgt_vlakken_merged;
