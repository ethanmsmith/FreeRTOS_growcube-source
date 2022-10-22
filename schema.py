from ariadne import gql


type_defs = gql(
    """
    type Query {
        plants: [Plant]
        settings: [Settings]
    }

    type Plant {
        commonName: String!
        genus: String!
        species: String!
    }

    type Settings {
        system: Config
        source: Config
        drain: Config
        food: Config
        air: Config
        LED: Config
    }

    type Config {
        delayOn: Int!
        delayOff: Int!
        pulseWidth: Int!
    }

    input ConfigInput {
        delayOn: Int!
        delayOff: Int!
        pulseWidth: Int!
    }

    type Mutation{ 
        add_plant( commonName: String!, genus: String!, species: String! ): Plant
        add_settings( system: ConfigInput!, source: ConfigInput, drain: ConfigInput, food: ConfigInput, air: ConfigInput, LED: ConfigInput ): Settings
        update_settings( id: ID!, system: ConfigInput!, source: ConfigInput, drain: ConfigInput, food: ConfigInput, air: ConfigInput, LED: ConfigInput ): Settings
    }
    """
)
