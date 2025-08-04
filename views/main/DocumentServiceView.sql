SELECT
  d.id AS documentId,
  s.id AS serviceId
FROM
  Document AS d
  JOIN Author AS a ON d.authorId = a.id
  JOIN Parliamentarian AS p ON a.parliamentarianId = p.id
  JOIN Service AS s ON s.parliamentarianId = p.id
WHERE
  d.date >= s.startDate
  AND (
    s.endDate IS NULL
    OR d.date <= s.endDate
  );