-- FUNCTION TO CREATE FISHNET
CREATE OR REPLACE FUNCTION ST_CreateFishnet(
        nrow integer, ncol integer,
        xsize float8, ysize float8,
        x0 float8 DEFAULT 0, y0 float8 DEFAULT 0,
        OUT "row" integer, OUT col integer,
        OUT geom geometry)
    RETURNS SETOF record AS
$$
SELECT i + 1 AS row, j + 1 AS col, ST_Translate(cell, j * $3 + $5, i * $4 + $6) AS geom
FROM generate_series(0, $1 - 1) AS i,
     generate_series(0, $2 - 1) AS j,
(
SELECT ('POLYGON((0 0, 0 '||$4||', '||$3||' '||$4||', '||$3||' 0,0 0))')::geometry AS cell
) AS foo;
$$ LANGUAGE sql IMMUTABLE STRICT;
/*
where nrow and ncol are the number of rows and columns, xsize and ysize are the lengths of the cell size, and optional x0 and y0 are coordinates for the bottom-left corner.
The result is row and col numbers, starting from 1 at the bottom-left corner, and geom rectangular polygons for each cell. 
*/
-- SOURCE: http://gis.stackexchange.com/questions/16374/how-to-create-a-regular-polygon-grid-in-postgis

CREATE OR REPLACE FUNCTION clean_multipolygon_minimum_area(
	geom geometry,
	area double precision DEFAULT 1.0)
    RETURNS geometry
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
	shorts int;
    BEGIN
	shorts = 1;
	WHILE shorts > 0
	LOOP
		WITH 
		polygons_dump AS (
			SELECT (ST_Dump($1)).geom geom
		), link AS (
			SELECT DISTINCT ON (s.geom) s.geom as s_geom, l.geom as l_geom 
			FROM polygons_dump l
			LEFT JOIN polygons_dump s
				ON ST_Overlaps(ST_exteriorring(s.geom),ST_Exteriorring(l.geom))
				AND ST_area(l.geom) > ST_Area(s.geom)
			WHERE ST_AREA(s.geom) < $2
			ORDER BY s.geom, ST_Area(l.geom) DESC, ST_Distance(s.geom,ST_Centroid(l.geom))
		), count_links AS (
			SELECT count(*) as shorts FROM link
		), new_geoms AS (
			SELECT ST_Buffer(ST_Collect(ST_Collect(s_geom),l_geom),0) geom
			FROM link
			WHERE l_geom NOT IN (SELECT s_geom FROM link)
			GROUP BY l_geom
			UNION
			SELECT b.geom
			FROM polygons_dump b
			WHERE b.geom NOT IN (SELECT l_geom FROM link)
				AND b.geom NOT IN (SELECT s_geom FROM link)
			UNION
			SELECT s_geom
			FROM link
			WHERE l_geom IN (SELECT s_geom FROM link)
		)
		SELECT ST_Collect(c.geom), max(d.shorts) into geom, shorts FROM new_geoms c, count_links d;
		--RAISE NOTICE 'shorts solved: %', shorts;
	END loop;
	RETURN geom;
    END;
$BODY$;

-----------------------------------

DROP TABLE IF EXISTS rechte_percelen_selectie; 
CREATE TABLE rechte_percelen_selectie AS
	SELECT 	id, 
			geom,
			ST_Rotate(
				geom, 
				ST_Azimuth(ST_PointN(ST_ExteriorRing(ST_OrientedEnvelope(geom)), 1), ST_PointN(ST_ExteriorRing(ST_OrientedEnvelope(geom)), 4)), 
				ST_Centroid(geom)
			) as geomgedraaid, 
			ST_Azimuth(ST_PointN(ST_ExteriorRing(ST_OrientedEnvelope(geom)), 1), ST_PointN(ST_ExteriorRing(ST_OrientedEnvelope(geom)), 4)) as draaihoek
	FROM 	kadastraal_perceel
	WHERE 	ST_Distance(
				ST_PointN(
					ST_ExteriorRing(
						ST_OrientedEnvelope(geom)
					), 
					1
				), 
				ST_PointN(
					ST_ExteriorRing(
						ST_OrientedEnvelope(geom)
					), 
					4
				)
			) > 75
;
CREATE INDEX ON rechte_percelen_selectie USING gist(geomgedraaid);
ALTER TABLE rechte_percelen_selectie ADD PRIMARY KEY (id);

DROP TABLE IF EXISTS fishnet;
CREATE TABLE fishnet AS 
	SELECT 	(	ST_CreateFishnet(
					CEIL((ST_YMax(ST_Extent(geomgedraaid))-ST_YMin(ST_Extent(geomgedraaid)))/75)::integer,
					CEIL((ST_YMax(ST_Extent(geomgedraaid))-ST_YMin(ST_Extent(geomgedraaid)))/75)::integer, 
					75, 
					75, 
					ST_XMin(ST_Extent(geomgedraaid)), 
					ST_YMin(ST_Extent(geomgedraaid))
				)
			).*
	FROM rechte_percelen_selectie
;
CREATE INDEX ON fishnet USING gist(geom);

DROP TABLE IF EXISTS geknipte_percelen_recht;
CREATE TABLE geknipte_percelen_recht AS
	SELECT	p.*, 
			ST_Intersection(ST_MakeValid(ST_SetSRID(p.geomgedraaid, 28992)), ST_SetSRID(fn.geom, 28992)) as geomsplit
	FROM 	rechte_percelen_selectie p 
	JOIN 	fishnet fn 
	ON 		ST_Intersects(p.geomgedraaid, ST_SetSRID(fn.geom, 28992)) 
;
CREATE INDEX ON geknipte_percelen_recht USING gist(geom); 

DROP TABLE IF EXISTS percelen_clean_teruggedraaid;
CREATE TABLE percelen_clean_teruggedraaid AS
WITH clean_polygons AS (
		SELECT  id, 
                clean_multipolygon_minimum_area(ST_Collect(geomsplit),100) as cgeom
		FROM 	geknipte_percelen_recht
		GROUP BY id
	)
, intersection_gedraaide_percelen_cleaned AS (
        SELECT  igp.*, 
                (ST_Dump(a.cgeom)).geom as cleangeom
        FROM clean_polygons a
        JOIN geknipte_percelen_recht AS igp ON a.id = igp.id)
SELECT 	id, 
		ST_Rotate(
			cleangeom, 
			(2*pi())-draaihoek,
			ST_Centroid(geom)
		) as geom
FROM intersection_gedraaide_percelen_cleaned
;

DROP TABLE IF EXISTS kadastraal_perceel_subdivided;
CREATE TABLE kadastraal_perceel_subdivided AS
WITH all_ids_and_geoms AS (
	SELECT id, geom FROM kadastraal_perceel
	WHERE ST_Distance(
				ST_PointN(
					ST_ExteriorRing(
						ST_OrientedEnvelope(geom)
					), 
					1
				), 
				ST_PointN(
					ST_ExteriorRing(
						ST_OrientedEnvelope(geom)
					), 
					4
				)
			) <= 75
	UNION 
	SELECT 	id, ST_Multi(geom) as geom
	FROM 	percelen_clean_teruggedraaid
	WHERE 	ST_GeometryType(geom) = 'ST_MultiPolygon' OR ST_GeometryType(geom) = 'ST_Polygon'
)
SELECT 	row_number() over() AS id, 
		ori.identificatielokaalid as brk_lokaalid, 
		ori.perceelnummer AS brk_perceelnummer,
        ST_Area(ori.geom) AS oppervlakte_perceel,
        NULL::text gemeentelijk_eigendom ,
        NULL::double precision oppervlakte_bebouwing ,
        NULL::double precision percentage_bebouwing ,
        NULL::double precision verhard_oppervlak,
        NULL::double precision verhard_percentage,
        NULL::double precision maaiveldhoogte,
        NULL::TEXT bodemsoort,
        NULL::double precision doorlatendheid_bodem,
        NULL::double precision ghg_tov_maaiveld ,
        NULL::double precision afstand_tot_bergingslocatie,
        NULL::TEXT code_dichtsbijzijnde_rioolleiding ,
        NULL::TEXT type_rioolstelsel ,
        NULL::TEXT kwetsbaarheid_oppervlaktewater,
        NULL::INTEGER aantal_keer_verpompen,
        NULL::TEXT afstand_tot_rwzi,
        NULL::TEXT type_gebied,
		ST_Force3D(ST_Multi(ST_Buffer(nw.geom,0)))::geometry(MultiPolygonZ, 28992) as geom
FROM 	kadastraal_perceel AS ori
JOIN	all_ids_and_geoms AS nw
	ON	ori.id = nw.id
;

CREATE INDEX ON kadastraal_perceel_subdivided USING gist(geom);
ALTER TABLE kadastraal_perceel_subdivided ADD PRIMARY KEY (id);

----- Cleaning up
DROP TABLE IF EXISTS fishnet;
DROP TABLE IF EXISTS rechte_percelen_selectie; 
DROP TABLE IF EXISTS geknipte_percelen_recht;
DROP TABLE IF EXISTS percelen_clean_teruggedraaid;
DROP TABLE IF EXISTS kadastraal_perceel;


