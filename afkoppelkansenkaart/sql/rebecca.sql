-- Criterium 1: percentage verhard

SELECT  perceel.id,
        zoek.score as score_criterium_1
FROM    percelen_scores AS perceel
LEFT JOIN    drempelwaardes_scores_criteria AS zoek
    ON  perceel."Percentage verhard" > zoek.ondergrens
        AND perceel."Percentage verhard" <= zoek.bovengrens
WHERE zoek.criterium = 1
;


UPDATE percelen_scores
SET "Score criterium 1" = (
    SELECT CASE
        WHEN "Percentage verhard" <= wad.k1_bovengrens THEN wad.k1_punten
        WHEN "Percentage verhard" > wad.k1_bovengrens AND "Percentage verhard" <= wad.k2_bovengrens THEN wad.k2_punten
        WHEN "Percentage verhard" > wad.k2_bovengrens AND "Percentage verhard" <= wad.k3_bovengrens THEN wad.k3_punten
        WHEN "Percentage verhard" > wad.k3_bovengrens AND "Percentage verhard" <= wad.k4_bovengrens THEN wad.k4_punten
    ELSE NULL
    END
    FROM    drempelwaardes_scores_criteria AS wad
    WHERE   criterium = 1)
;

-- Criterium 2
UPDATE percelen_scores
	SET "Score criterium 2" = (SELECT CASE
									WHEN "Percentage bebouwing" <= wad.k1_bovengrens THEN wad.k1_punten
									WHEN "Percentage bebouwing" > wad.k1_bovengrens AND "Percentage bebouwing" <= wad.k2_bovengrens THEN wad.k2_punten
									WHEN "Percentage bebouwing" > wad.k2_bovengrens AND "Percentage bebouwing" <= wad.k3_bovengrens THEN wad.k3_punten
									WHEN "Percentage bebouwing" > wad.k3_bovengrens AND "Percentage bebouwing" <= wad.k4_bovengrens THEN wad.k4_punten
									ELSE NULL
 							END
							FROM drempelwaardes_scores_criteria AS wad
							WHERE criterium = 2);

-- Criterium 3
UPDATE percelen_scores
	SET "Score criterium 3" = (SELECT CASE
									WHEN "GHG beneden maaiveld" <= wad.k1_bovengrens THEN wad.k1_punten
									WHEN "GHG beneden maaiveld" > wad.k1_bovengrens AND "GHG beneden maaiveld" <= wad.k2_bovengrens THEN wad.k2_punten
									WHEN "GHG beneden maaiveld" > wad.k2_bovengrens AND "GHG beneden maaiveld" <= wad.k3_bovengrens THEN wad.k3_punten
									ELSE NULL
 							END
							FROM drempelwaardes_scores_criteria AS wad
							WHERE criterium = 3);

-- Criterium 4
UPDATE percelen_scores
	SET "Score criterium 4" = (SELECT CASE
									WHEN "Doorlatendheid bodem" <= wad.k1_bovengrens THEN wad.k1_punten
									WHEN "Doorlatendheid bodem" > wad.k1_bovengrens AND "Doorlatendheid bodem" <= wad.k2_bovengrens THEN wad.k2_punten
									WHEN "Doorlatendheid bodem" > wad.k2_bovengrens AND "Doorlatendheid bodem" <= wad.k3_bovengrens THEN wad.k3_punten
									WHEN "Doorlatendheid bodem" > wad.k3_bovengrens AND "Doorlatendheid bodem" <= wad.k4_bovengrens THEN wad.k4_punten
									ELSE NULL
 							END
							FROM drempelwaardes_scores_criteria AS wad
							WHERE criterium = 4);


-- Criterium 5
UPDATE percelen_scores
	SET "Score criterium 5" = (SELECT CASE
									WHEN "Afstand tot bergingslocatie" <= wad.k1_bovengrens THEN wad.k1_punten
									WHEN "Afstand tot bergingslocatie" > wad.k1_bovengrens AND "Afstand tot bergingslocatie" <= wad.k2_bovengrens THEN wad.k2_punten
									WHEN "Afstand tot bergingslocatie" > wad.k2_bovengrens AND "Afstand tot bergingslocatie" <= wad.k3_bovengrens THEN wad.k3_punten
									WHEN "Afstand tot bergingslocatie" IS NULL THEN wad.k4_punten
									ELSE NULL
 							END
							FROM drempelwaardes_scores_criteria AS wad
							WHERE criterium = 5);



-- Criterum 6
UPDATE percelen_scores
	SET "Score criterium 6" = (SELECT CASE
									WHEN "Type rioolstelsel" = cac.k1_omschrijving THEN cac.k1_punten
									WHEN "Type rioolstelsel" = cac.k2_omschrijving THEN cac.k2_punten
									WHEN "Type rioolstelsel" = cac.k3_omschrijving THEN cac.k3_punten
									WHEN "Type rioolstelsel" = cac.k4_omschrijving THEN cac.k4_punten
									WHEN "Type rioolstelsel" = cac.k5_omschrijving THEN cac.k5_punten
									WHEN "Type rioolstelsel" = cac.k6_omschrijving THEN cac.k6_punten
									ELSE NULL
 							END
							FROM categorie_scores_criteria AS cac
							WHERE criterium = 6);


-- Criterum 7
UPDATE percelen_scores
	SET "Score criterium 7" = (SELECT CASE
									WHEN "Aantal keer verpompen" <= wad.k1_bovengrens THEN wad.k1_punten
									WHEN "Aantal keer verpompen" > wad.k1_bovengrens AND "Aantal keer verpompen" <= wad.k2_bovengrens THEN wad.k2_punten
									WHEN "Aantal keer verpompen" > wad.k2_bovengrens AND "Aantal keer verpompen" <= wad.k3_bovengrens THEN wad.k3_punten
									WHEN "Aantal keer verpompen" IS NULL THEN wad.k4_punten
									ELSE NULL
 							END
							FROM drempelwaardes_scores_criteria AS wad
							WHERE criterium = 7);

-- Criterium 8
UPDATE percelen_scores
	SET "Score criterium 8" = (SELECT CASE
									WHEN "Afstand tot RWZI" <= wad.k1_bovengrens THEN wad.k1_punten
									WHEN "Afstand tot RWZI" > wad.k1_bovengrens AND "Afstand tot RWZI" <= wad.k2_bovengrens THEN wad.k2_punten
									WHEN "Afstand tot RWZI" > wad.k2_bovengrens AND "Afstand tot RWZI" <= wad.k3_bovengrens THEN wad.k3_punten
									WHEN "Afstand tot RWZI" IS NULL THEN wad.k4_punten
									ELSE NULL
 							END
							FROM drempelwaardes_scores_criteria AS wad
							WHERE criterium = 8);

-- Criterum 9
UPDATE percelen_scores
SET "Score criterium 9" = (SELECT CASE
									WHEN "Kwetsbaarheid opp water" = cac.k1_omschrijving THEN cac.k1_punten
									WHEN "Kwetsbaarheid opp water" = cac.k2_omschrijving THEN cac.k2_punten
									WHEN "Kwetsbaarheid opp water" = cac.k3_omschrijving THEN cac.k3_punten
									WHEN "Kwetsbaarheid opp water" = cac.k4_omschrijving THEN cac.k4_punten
									WHEN "Kwetsbaarheid opp water" = cac.k5_omschrijving THEN cac.k5_punten
									WHEN "Kwetsbaarheid opp water" IS NULL THEN cac.k6_punten
									ELSE NULL
 							END
							FROM categorie_scores_criteria AS cac
							WHERE criterium = 9
);

-- Criterium 10
UPDATE percelen_scores
	SET "Score criterium 10" = (SELECT CASE
									WHEN "Type gebied" = cac.k1_omschrijving THEN cac.k1_punten
									WHEN "Type gebied" = cac.k2_omschrijving THEN cac.k2_punten
									WHEN "Type gebied" = cac.k3_omschrijving THEN cac.k3_punten
									ELSE NULL
 							END
							FROM categorie_scores_criteria AS cac
							WHERE criterium = 10);


-- Criterium 11
UPDATE percelen_scores
	SET "Score criterium 11" = (SELECT CASE
									WHEN "Verhard oppervlak" <= wad.k1_bovengrens THEN wad.k1_punten
									WHEN "Verhard oppervlak" > wad.k1_bovengrens AND "Verhard oppervlak" <= wad.k2_bovengrens THEN wad.k2_punten
									WHEN "Verhard oppervlak" > wad.k2_bovengrens AND "Verhard oppervlak" <= wad.k3_bovengrens THEN wad.k3_punten
									WHEN "Verhard oppervlak" > wad.k3_bovengrens AND "Verhard oppervlak" <= wad.k4_bovengrens THEN wad.k4_punten
									ELSE NULL
 							END
							FROM drempelwaardes_scores_criteria AS wad
							WHERE criterium = 11);




-- Score domein opp water
UPDATE percelen_scores
	SET "Score domein opp water" = "Score criterium 9"
	;

-- Score domein verharding
UPDATE percelen_scores
	SET "Score domein verharding" = ROUND(("Score criterium 1" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Criterium 1'))
													+  ("Score criterium 2" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Criterium 2')) , 3)
	;


-- Score domein efficientie
UPDATE percelen_scores
	SET "Score domein efficientie" = "Score criterium 11"
	;

-- Score domein transport
UPDATE percelen_scores
	SET "Score domein transport" = ROUND(("Score criterium 6" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Criterium 6'))
												+  ("Score criterium 7" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Criterium 7'))
												+  ("Score criterium 8" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Criterium 8')) , 3)
	;

-- Score domein afstand
UPDATE percelen_scores
	SET "Score domein afstand" = "Score criterium 5"

-- Score domein wateroverlast
UPDATE percelen_scores
	SET "Score domein wateroverlast" = "Score criterium 10"
	;

-- Score domein effectiviteit
UPDATE percelen_scores
	SET "Score effectiviteit" = ROUND(("Score domein efficientie" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Domein efficientie'))
												+  ("Score domein opp water" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Domein opp water'))
												+ ("Score domein transport" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Domein transport'))
												+ ("Score domein wateroverlast" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Domein wateroverlast')) , 3);

-- Score domein infiltratie
UPDATE percelen_scores
	SET "Score domein infiltratie" =ROUND(("Score criterium 3" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Criterium 3'))
												+  ("Score criterium 4" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Criterium 4')), 3)
	;

-- Score fysieke kansrijkheid
UPDATE percelen_scores
	SET "Score fysieke kansrijkheid" = ROUND(("Score domein afstand" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Domein afstand'))
												+  ("Score domein infiltratie" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Domein infiltratie'))
												+ ("Score domein verharding" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Domein verharding')) , 3);
-- Eindscore
UPDATE percelen_scores
	SET "Eindscore" = ROUND(("Score fysieke kansrijkheid" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Fysieke kansrijkheid'))
													+ ("Score effectiviteit" * (SELECT "Wegingsfactor" FROM wegingsfactoren WHERE "Naam" = 'Effectiviteit')) , 3);

-- Gemiddelde score per wijk
UPDATE wijken_gemiddelde_score
SET "Gemiddelde eindscore" = (SELECT ROUND(SUM(perc."Oppervlakte perceel" * perc."Eindscore")/SUM(perc."Oppervlakte perceel"),3) FROM percelen_scores AS perc
WHERE ST_Intersects(perc.geom, wijken_gemiddelde_score.geom)
GROUP BY "Wijknaam")
UPDATE buurten_gemiddelde_score
SET "Gemiddelde eindscore" = (SELECT ROUND(SUM(perc."Oppervlakte perceel" * perc."Eindscore")/SUM(perc."Oppervlakte perceel"),3) FROM percelen_scores AS perc
WHERE ST_Intersects(perc.geom, buurten_gemiddelde_score.geom)
GROUP BY "Buurtnaam")
