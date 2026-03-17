-- Source definitions matching scripts/seed.py
local sources = {
    { id = 1, name = "Hansard 1901-1980" },
    { id = 2, name = "Hansard 1981-1991" },
    { id = 3, name = "Hansard 1992-1996" },
    { id = 4, name = "Hansard 1997" },
    { id = 5, name = "Hansard 1998-1999" },
    { id = 6, name = "Hansard 2000-2011" },
    { id = 7, name = "Hansard 2011" },
    { id = 8, name = "Hansard 2012-2021" },
    { id = 9, name = "Hansard 2021-Present" },
}

local tasks = {
    {
        name = "Up DB",
        builder = function(_)
            return {
                cmd = { "docker", "compose", "up", "db" },
                components = { "default" },
            }
        end,
    },

    {
        name = "Prisma Studio",
        builder = function(_)
            return {
                cmd = { "docker", "compose", "up", "--build", "studio" },
                components = { "default" },
            }
        end,
    },
    {
        name = "Download DB",
        builder = function(_)
            return {
                cmd = { "docker", "compose", "run", "download" },
                components = { "default" },
            }
        end,
    },
    {
        name = "Upload DB",
        builder = function(_)
            return {
                cmd = { "docker", "compose", "run", "upload" },
                components = { "default" },
            }
        end,
    },
    {
        name = "Update DB",
        builder = function(_)
            return {
                cmd = { "docker", "compose", "run", "--build", "update" },
                components = { "default" },
            }
        end,
    },

    {
        name = "Reparse DB",
        builder = function(_)
            return {
                cmd = { "docker", "compose", "run", "--build", "update", "scripts/update.py", "--reparse" },
                components = { "default" },
            }
        end,
    },

    {
        name = "Reset DB",
        builder = function(_)
            return {
                cmd = { "python3", "-m", "prisma", "migrate", "reset", "--force" },
                components = { "default" },
            }
        end,
    },

    {
        name = "Open DB Client",
        builder = function(_)
            return {
                cmd = { "pgcli", "postgresql://prisma_user:prisma_password@localhost:5432/prisma_db" },
                components = {
                    { "open_output", direction = "float", on_start = "always", focus = true },
                    "default"
                },
            }
        end,
    },

    {
        name = "Parser Report",
        builder = function(_)
            return {
                cmd = { "python3", "tests/run_report.py" },
                components = {
                    { "open_output", direction = "float", on_start = "always", focus = true },
                    "default"
                },
            }
        end,
    },
}

-- Generate Update and Reparse tasks for each source
for _, source in ipairs(sources) do
    table.insert(tasks, {
        name = "Update " .. source.name,
        builder = function(_)
            return {
                cmd = { "docker", "compose", "run", "--build", "update", "scripts/update.py", "--source-id", tostring(source.id) },
                components = { "default" },
            }
        end,
    })

    table.insert(tasks, {
        name = "Reparse " .. source.name,
        builder = function(_)
            return {
                cmd = { "docker", "compose", "run", "--build", "update", "scripts/update.py", "--reparse", "--source-id", tostring(source.id) },
                components = { "default" },
            }
        end,
    })
end

return tasks
