from OpenGLContext.scenegraph.basenodes import Sphere
from OpenGL.GL import shaders
from OpenGLContext.arrays import *
from OpenGL.arrays import vbo
from OpenGL.GL import *
from OpenGLContext import testingcontext
BaseContext = testingcontext.getInteractive()


class TestContext(BaseContext):
    """Demonstrates use of attribute types in GLSL
    """
    uniform_locations = []
    attribute_locations = []

    def var_uniform(self, typename, name, register=True):
        if register:
            self.uniform_locations.append(name)
        return "uniform %s %s;" % (typename, name)

    def var_attribute(self, typename, name, register=True):
        if register:
            self.attribute_locations.append(name)
        return "attribute %s %s;" % (typename, name)

    def var_varying(self, typename, name):
        return "varying %s %s;" % (typename, name)

    def OnInit(self):
        """Initialize the context"""
        phong_weightCalc = """
        vec2 phong_weightCalc(
            in vec3 light_pos, // light position
            in vec3 half_light, // half-way vector between light and view
            in vec3 frag_normal, // geometry normal
            in float shininess
        ) {
            // returns vec2( ambientMult, diffuseMult )
            float n_dot_pos = max( 0.0, dot(
                frag_normal, light_pos
            ));
            float n_dot_half = 0.0;
            if (n_dot_pos > -.05) {
                n_dot_half = pow(max(0.0,dot(
                    half_light, frag_normal
                )), shininess);
            }
            return vec2( n_dot_pos, n_dot_half);
        }
        """

        vertex = shaders.compileShader(
            self.var_attribute('vec3', 'Vertex_position') +
            self.var_attribute('vec3', 'Vertex_normal') +
            self.var_varying('vec3', 'baseNormal') +
            """
        void main() {
            gl_Position = gl_ModelViewProjectionMatrix * vec4(
                Vertex_position, 1.0
            );
            baseNormal = gl_NormalMatrix * normalize(Vertex_normal);
        }""", GL_VERTEX_SHADER)

        fragment = shaders.compileShader(
            phong_weightCalc +
            self.var_uniform('vec4', 'Global_ambient') +
            self.var_uniform('vec4', 'Light_ambient') +
            self.var_uniform('vec4', 'Light_diffuse') +
            self.var_uniform('vec4', 'Light_specular') +
            self.var_uniform('vec3', 'Light_location') +
            self.var_uniform('float', 'Material_shininess') +
            self.var_uniform('vec4', 'Material_specular') +
            self.var_uniform('vec4', 'Material_ambient') +
            self.var_uniform('vec4', 'Material_diffuse') +
            self.var_varying('vec3', 'baseNormal') +
            """
        void main() {
            // normalized eye-coordinate Light location
            vec3 EC_Light_location = normalize(
                gl_NormalMatrix * Light_location
            );
            // half-vector calculation
            vec3 Light_half = normalize(
                EC_Light_location - vec3( 0,0,-1 )
            );
            vec2 weights = phong_weightCalc(
                EC_Light_location,
                Light_half,
                baseNormal,
                Material_shininess
            );
            gl_FragColor = clamp(
            (
                (Global_ambient * Material_ambient)
                + (Light_ambient * Material_ambient)
                + (Light_diffuse * Material_diffuse * weights.x)
                // material's shininess is the only change here...
                + (Light_specular * Material_specular * weights.y)
            ), 0.0, 1.0);
        }
        """, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vertex, fragment)

        self.coords, self.indices, self.count = Sphere(
            radius=1
        ).compile()

        self.getUniformLocations(self.uniform_locations)
        self.getAttribLocations(self.attribute_locations)

    def getUniformLocations(self, uniform_locations):
        for uniform in uniform_locations:
            location = glGetUniformLocation(self.shader, uniform)
            if location in (None, -1):
                print '[Warning], no uniform location %s' % (uniform)
            setattr(self, uniform+'_loc', location)

    def getAttribLocations(self, attrib_locations):
        for attrib in attrib_locations:
            location = glGetAttribLocation(self.shader, attrib)
            if location in (None, -1):
                print '[Warning], no attrib location %s' % (attrib)
            setattr(self, attrib+'_loc', location)

    def Render(self, mode=None):
        """Render the geometry for the scene."""
        BaseContext.Render(self, mode)
        glUseProgram(self.shader)
        try:
            self.coords.bind()
            self.indices.bind()
            stride = self.coords.data[0].nbytes
            try:
                glUniform4f(self.Global_ambient_loc, .05, .05, .05, .1)
                glUniform4f(self.Light_ambient_loc, .1, .1, .1, 1.0)
                glUniform4f(self.Light_diffuse_loc, .25, .25, .25, 1)
                glUniform4f(self.Light_specular_loc, 0.0, 1.0, 0, 1)
                glUniform3f(self.Light_location_loc, 6, 2, 4)
                glUniform4f(self.Material_ambient_loc, .1, .1, .1, 1.0)
                glUniform4f(self.Material_diffuse_loc, .15, .15, .15, 1)
                glUniform4f(self.Material_specular_loc, 1.0, 1.0, 1.0, 1.0)
                glUniform1f(self.Material_shininess_loc, .95)
                for attrib in self.attribute_locations:
                    glEnableVertexAttribArray(getattr(self, attrib+'_loc'))

                hop = 5*4
                for i, attrib in enumerate(self.attribute_locations):
                    glVertexAttribPointer(
                        getattr(self, attrib+'_loc'),
                        3, GL_FLOAT, False, stride, self.coords + (i*hop)
                    )

                glDrawElements(
                    GL_TRIANGLES, self.count,
                    GL_UNSIGNED_SHORT, self.indices
                )
            finally:
                self.coords.unbind()
                self.indices.unbind()
                for attrib in self.attribute_locations:
                    glDisableVertexAttribArray(getattr(self, attrib+'_loc'))
        finally:
            glUseProgram(0)


if __name__ == "__main__":
    TestContext.ContextMainLoop()
