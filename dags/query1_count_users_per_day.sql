SELECT
    signup_date,
    COUNT(*) AS user_count
FROM
    users
GROUP BY
    signup_date
ORDER BY
    signup_date;