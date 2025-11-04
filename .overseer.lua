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
                cmd = { "docker", "compose", "run", "studio" },
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
                cmd = { "docker", "compose", "run", "update" },
                components = { "default" },
            }
        end,
    },

    {
        name = "Update DB",
        builder = function(_)
            return {
                cmd = { "docker", "compose", "run", "reparse" },
                components = { "default" },
            }
        end,
    },
}
