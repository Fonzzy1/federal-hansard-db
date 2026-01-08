return {
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
}
