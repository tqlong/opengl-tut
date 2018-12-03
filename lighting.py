from OpenGLContext import testingcontext
from OpenGLContext.arrays import *
from OpenGLContext.events.timer import Timer
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays import vbo

BaseContext = testingcontext.getInteractive()


class TestContext (BaseContext):
    uniform_locations = []
    attribute_locations = []
    hop = {'Vertex_position': 0, 'Vertex_normal': 12}

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
        phong_weightCalc = """
        float phong_weightCalc(
            in vec3 light_pos,
            in vec3 frag_normal
        ) {
            float n_dot_pos = max(0.0, dot(frag_normal, light_pos));
            return n_dot_pos;
        }
        """
        VERTEX_SHADER = shaders.compileShader(
            phong_weightCalc +
            self.var_uniform("vec4", "Global_ambient") +
            self.var_uniform("vec4", "Light_ambient") +
            self.var_uniform("vec4", "Light_diffuse") +
            self.var_uniform("vec3", "Light_location") +
            self.var_uniform("vec4", "Material_ambient") +
            self.var_uniform("vec4", "Material_diffuse") +
            self.var_attribute("vec3", "Vertex_position") +
            self.var_attribute("vec3", "Vertex_normal") +
            self.var_varying("vec4", "baseColor") +
            """
        void main() {
            gl_Position = gl_ModelViewProjectionMatrix * vec4(Vertex_position, 1.0);
            vec3 EC_Light_location = gl_NormalMatrix * Light_location;
            float diffuse_weight = phong_weightCalc(
                normalize(EC_Light_location),
                normalize(gl_NormalMatrix * Vertex_normal)
            );
            baseColor = clamp(
                (Global_ambient * Material_ambient)
                + (Light_ambient * Material_ambient)
                + (Light_diffuse * Material_diffuse * diffuse_weight )
            , 0.0, 1.0);
        }""", GL_VERTEX_SHADER)

        FRAGMENT_SHADER = shaders.compileShader(
            self.var_varying("vec4", "baseColor") +
            """
        void main() {
            gl_FragColor = baseColor;
        }""", GL_FRAGMENT_SHADER)

        self.shader = shaders.compileProgram(VERTEX_SHADER, FRAGMENT_SHADER)

        self.vbo = vbo.VBO(
            array([
                [-1, 0, 0, -1, 0, 1],
                [0, 0, 1, -1, 0, 2],
                [0, 1, 1, -1, 0, 2],
                [-1, 0, 0, -1, 0, 1],
                [0, 1, 1, -1, 0, 2],
                [-1, 1, 0, -1, 0, 1],
                [0, 0, 1, -1, 0, 2],
                [1, 0, 1, 1, 0, 2],
                [1, 1, 1, 1, 0, 2],
                [0, 0, 1, -1, 0, 2],
                [1, 1, 1, 1, 0, 2],
                [0, 1, 1, -1, 0, 2],
                [1, 0, 1, 1, 0, 2],
                [2, 0, 0, 1, 0, 1],
                [2, 1, 0, 1, 0, 1],
                [1, 0, 1, 1, 0, 2],
                [2, 1, 0, 1, 0, 1],
                [1, 1, 1, 1, 0, 2],
            ], 'f')
        )

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

    def Render(self, mode):
        BaseContext.Render(self, mode)
        shaders.glUseProgram(self.shader)
        # set GPU uniform (global) variable tween to have value of self.tween_fraction

        try:
            self.vbo.bind()
            try:
                glUniform4f(self.Global_ambient_loc, .3, .05, .05, .1)
                glUniform4f(self.Light_ambient_loc, .2, .2, .2, 1.0)
                glUniform4f(self.Light_diffuse_loc, 1, 1, 1, 1)
                glUniform3f(self.Light_location_loc, 2, 2, 10)
                glUniform4f(self.Material_ambient_loc, .2, .2, .2, 1.0)
                glUniform4f(self.Material_diffuse_loc, 1, 1, 1, 1)
                for k in self.hop:
                    glEnableVertexAttribArray(getattr(self, k+'_loc'))

                # set data (position, tweened, color) using self.vbo array
                stride = 6*4
                for k, v in self.hop.items():
                    glVertexAttribPointer(
                        getattr(self, k+'_loc'), 3, GL_FLOAT, False, stride, self.vbo+v)

                glDrawArrays(GL_TRIANGLES, 0, 18)
            finally:
                self.vbo.unbind()
                for k in self.hop:
                    glDisableVertexAttribArray(getattr(self, k+'_loc'))
        finally:
            shaders.glUseProgram(0)


if __name__ == "__main__":
    TestContext.ContextMainLoop()
