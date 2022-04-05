-- BOFEK BODEM RASTER STATISTICS OMZETTEN IN TEKST
ALTER TABLE kadastraal_perceel_subdivided ADD COLUMN IF NOT EXISTS bodemsoort text;
ALTER TABLE kadastraal_perceel_subdivided ADD COLUMN IF NOT EXISTS doorlatendheid_bodem double precision;

UPDATE 	kadastraal_perceel_subdivided AS perc
SET 	bodemsoort = bofek_vertaaltabel.beschrijving
FROM 	bofek, 
		bofek_vertaaltabel
WHERE 	perc.id = bofek.id 
		AND bofek.pawn_code_majority = bofek_vertaaltabel.pawn_code
; 
