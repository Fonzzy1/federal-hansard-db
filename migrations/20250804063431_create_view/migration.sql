CREATE VIEW DocumentServiceFilterView AS
SELECT
    d.id                 AS documentId,
    d.date               AS documentDate,
    s.id                 AS serviceId,
    s.parliamentId       AS parliamentId,
    par.firstDate        AS parliamentFirstDate,
    par.lastDate         AS parliamentLastDate,
    s.partyId            AS partyId,
    party.name           AS partyName,
    s.seat               AS seat,
    s.state              AS state,
    s.isSenate           AS isSenate,
    p.id                 AS parliamentarianId,
    p.firstName          AS firstName,
    p.lastName           AS lastName,
    p.firstNations       AS firstNations,
    p.gender             AS gender,
    p.dob                AS dob
FROM Document d
JOIN Author a ON d.authorId = a.id
JOIN Parliamentarian p ON a.parliamentarianId = p.id
JOIN Service s ON s.parliamentarianId = p.id
JOIN Parliament par ON par.id = s.parliamentId
JOIN Party party ON party.id = s.partyId
WHERE d.date >= s.startDate
  AND (s.endDate IS NULL OR d.date <= s.endDate);
